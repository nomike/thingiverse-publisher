# thingiverse-publisher - A simple script to publish things to Thingiverse using the Thingiverse API.
# (C) 2024 - nomike[at]nomike[dot]com
# GPL-3.0-or-later

"""
Usage:
    thingiverse-publisher [options]
    thingiverse-publisher [-h | --help]

Options:
    -b --bearer-token=<token>   The bearer token to authenticate with the Thingiverse API.
    -u --username=<username>    The username of the Thingiverse account to use.
    -h --help                   Show this screen.
    -v --verbose                Show debug information.

This script provides functionality to publish things to Thingiverse using the Thingiverse API.
It allows users to create or update a thing on Thingiverse, upload files associated with the thing,
and handle errors during the process.

The script requires a configuration file named '.thingiverse_publisher.json' in the current directory,
which contains the necessary information such as the bearer token, thing details, and file paths.

The script uses the 'docopt' library to parse command-line arguments and the 'thingiverse-client' SDK
for API requests.
"""

import json
import logging
import os
from datetime import datetime

import httpx
from docopt import docopt
from thingiverse import BASE_URL_PRODUCTION, AuthenticatedClient
from thingiverse.api.thing import (
    delete_things_thing_id_files_file_id,
    delete_things_thing_id_images_image_id,
    get_things_thing_id_files_file_id,
    get_things_thing_id_images_image_id,
    patch_things_thing_id,
    post_things,
)
from thingiverse.api.user import get_users_username_things
from thingiverse.models.patch_things_thing_id_body import PatchThingsThingIdBody
from thingiverse.models.post_things_body import PostThingsBody
from thingiverse.models.post_things_body_license import PostThingsBodyLicense
from thingiverse.types import UNSET

from thingiverse_publisher import __version__

local_config: dict = {}
config: dict = {}
client: AuthenticatedClient | None = None


def _thing_client() -> AuthenticatedClient:
    """Return the authenticated client. Must be called after main() has set up client."""
    if client is None:
        raise RuntimeError("Client not initialized")
    return client


def check_file_mtime(file_path: str, type: str) -> bool:
    thing_id = config["thing"]["id"]
    file_id = config[f"{type}s"][file_path]["id"]
    api_client = _thing_client()

    if type == "file":
        response = get_things_thing_id_files_file_id.sync_detailed(
            thing_id=thing_id, file_id=file_id, client=api_client
        )
        _raise_for_status(response)
        file_schema = response.parsed
        if (
            not hasattr(file_schema, "date")
            or file_schema.date is None
            or file_schema.date is UNSET
        ):
            return True
        thingiverse_mtime = datetime.fromisoformat(str(file_schema.date).replace("Z", "+00:00"))
    elif type == "image":
        response = get_things_thing_id_images_image_id.sync_detailed(
            thing_id=thing_id,
            image_id=file_id,
            client=api_client,
            size="small",
            type_="display",
        )
        _raise_for_status(response)
        # Response 200 is a flexible object with "added" in additional_properties
        img = response.parsed
        added = getattr(img, "additional_properties", {}).get("added", "") if img else ""
        if not added:
            return True
        thingiverse_mtime = datetime.fromisoformat(str(added).replace("Z", "+00:00"))
    else:
        raise ValueError(f"Unknown type: {type}")

    local_mtime = datetime.fromtimestamp(os.path.getmtime(file_path)).astimezone()
    logging.debug("Local mtime: %s", local_mtime)
    logging.debug("Thingiverse mtime: %s", thingiverse_mtime.astimezone())
    return local_mtime > thingiverse_mtime.astimezone()


def upload_image_or_file(file_path: str, type: str) -> None:
    global local_config
    api_client = _thing_client()
    thing_id = config["thing"]["id"]

    if "id" in local_config[f"{type}s"][file_path]:
        if check_file_mtime(file_path, type):
            logging.info(
                "Local %s is newer than the one on Thingiverse. Deleting old %s...",
                type,
                type,
            )
            file_id = config[f"{type}s"][file_path]["id"]
            if type == "file":
                resp = delete_things_thing_id_files_file_id.sync_detailed(
                    thing_id=thing_id, file_id=file_id, client=api_client
                )
            else:
                resp = delete_things_thing_id_images_image_id.sync_detailed(
                    thing_id=thing_id, image_id=file_id, client=api_client
                )
            _raise_for_status(resp, ok=(200, 204))
        else:
            logging.info(
                '%s "%s" already exists on Thingiverse. Skipping upload.',
                type.capitalize(),
                file_path,
            )
            return

    logging.info(
        "%s %s does not exist on Thingiverse or local %s is newer. Uploading...",
        type.capitalize(),
        file_path,
        type,
    )

    logging.info('Requesting upload for %s "%s"...', type, file_path)
    httpx_client = api_client.get_httpx_client()
    prepare_response = httpx_client.post(
        f"/things/{thing_id}/files",
        json={"filename": os.path.basename(file_path)},
    )
    logging.debug("Response status code: %s", prepare_response.status_code)
    prepare_response.raise_for_status()
    prepare_data = prepare_response.json()
    logging.debug("Response data: %s", json.dumps(prepare_data, indent=2))
    logging.info("File upload requested.")

    logging.info("Uploading %s %s...", type, file_path)
    with open(file_path, "rb") as f:
        upload_response = httpx.post(
            prepare_data["action"],
            files={"file": f},
            data=prepare_data["fields"],
        )
    logging.debug("Response status code: %s", upload_response.status_code)
    upload_response.raise_for_status()
    logging.info("%s uploaded successfully!", type.capitalize())

    logging.info("Calling finalizer...")
    finalize_response = httpx_client.post(
        prepare_data["fields"]["success_action_redirect"],
        data=prepare_data["fields"],
    )
    logging.debug("Response status code: %s", finalize_response.status_code)
    finalize_response.raise_for_status()
    local_config[f"{type}s"][file_path] = finalize_response.json()


def upload_image(image_path: str) -> None:
    upload_image_or_file(image_path, "image")


def upload_file(file_path: str) -> None:
    upload_image_or_file(file_path, "file")


def _thing_to_post_body(thing: dict) -> PostThingsBody:
    """Build PostThingsBody from config thing dict (without id)."""
    license_val = thing.get("license", "cc")
    try:
        license_enum = PostThingsBodyLicense(license_val)
    except ValueError:
        license_enum = PostThingsBodyLicense.CC
    return PostThingsBody(
        name=thing["name"],
        category=thing.get("category", "Other"),
        license_=license_enum,
        description=thing.get("description", UNSET),
        instructions=thing.get("instructions", UNSET),
        tags=thing.get("tags", UNSET),
        ancestors=thing.get("ancestors", UNSET),
        is_wip=thing.get("is_wip", UNSET),
        is_customizer=thing.get("is_customizer", UNSET),
        is_remix=thing.get("is_remix", UNSET),
    )


def _thing_to_patch_body(thing: dict) -> PatchThingsThingIdBody:
    """Build PatchThingsThingIdBody from config thing dict (only updatable fields)."""
    patch_keys = {
        "name",
        "description",
        "instructions",
        "category",
        "license",
        "is_wip",
        "is_remix",
        "tags",
        "ancestors",
    }
    return PatchThingsThingIdBody.from_dict(
        {k: v for k, v in thing.items() if k in patch_keys and v is not None}
    )


def _raise_for_status(response: object, ok: tuple[int, ...] = (200,)) -> None:
    """Raise if response status is not in the allowed success set."""
    status = getattr(response, "status_code", None)
    if status is not None and status not in ok:
        content = getattr(response, "content", b"")
        msg = content.decode("utf-8", errors="replace") if content else ""
        request = getattr(response, "request", None)
        raise httpx.HTTPStatusError(
            f"Server error {status}: {msg}",
            request=request,
            response=httpx.Response(status_code=status, content=content),
        )


def create_or_update_thing() -> None:
    """
    Creates or updates a thing on Thingiverse based on the provided configuration.

    This function checks if the thing already exists on Thingiverse by searching for a matching name.
    If the thing exists, it updates the existing thing with the provided configuration.
    If the thing does not exist, it creates a new thing with the provided configuration.

    The function also uploads files associated with the thing.

    Raises:
        ValueError: If more than one thing with the same name is found on Thingiverse.

    """
    global local_config, config
    api_client = _thing_client()

    try:
        if "id" not in config["thing"]:
            logging.info("No ID found in config. Checking if thing already exists...")
            logging.debug("List all things owned by %s...", config["username"])
            response = get_users_username_things.sync_detailed(
                username=config["username"], client=api_client
            )
            _raise_for_status(response)
            data = response.parsed
            if not isinstance(data, list):
                raise RuntimeError("Unexpected response type from get users things")
            logging.debug("Response data: %s", json.dumps([t.to_dict() for t in data], indent=2))

            matching_things = [t for t in data if t.name == config["thing"]["name"]]
            if len(matching_things) > 1:
                raise ValueError(
                    f"More than one thing with name {config['thing']['name']} found. "
                    "Please delete all but one."
                )
            if len(matching_things) == 1:
                logging.info(
                    "Thing with name %s already exists. Using id %s.",
                    config["thing"]["name"],
                    matching_things[0].id,
                )
                local_config["thing"]["id"] = matching_things[0].id
                config["thing"]["id"] = matching_things[0].id
            else:
                logging.info(
                    "No thing with name %s found. New thing will be created.",
                    config["thing"]["name"],
                )

        if "id" not in config["thing"]:
            logging.info("Thing does not exist, creating a new one...")
            body = _thing_to_post_body(config["thing"])
            response = post_things.sync_detailed(client=api_client, body=body)
            _raise_for_status(response, ok=(200, 201))
            created = response.parsed
            if created is None:
                raise RuntimeError(
                    "post_things returned success but SDK did not parse response body"
                )
            created_id = getattr(created, "id", None)
            if created_id is None:
                raise RuntimeError("post_things response missing id")
            config["thing"]["id"] = created_id
            logging.info("Thing created successfully!")
            logging.debug("Response data: %s", response.parsed)
        else:
            logging.info(
                "Thing does exist. Patching existing thing with ID %s...",
                config["thing"]["id"],
            )
            body = _thing_to_patch_body(config["thing"])
            response = patch_things_thing_id.sync_detailed(
                thing_id=config["thing"]["id"], client=api_client, body=body
            )
            _raise_for_status(response)
            logging.info("Thing patched successfully!")
            logging.debug("Response data: %s", response.parsed)

        logging.info("Uploading files...")
        for file in config["files"]:
            upload_file(file)
        logging.info("Uploading images...")
        for file in config["images"]:
            upload_image(file)

    except httpx.HTTPError as e:
        print("Error:", e)
        if getattr(e, "response", None) is not None:
            print(
                "Upstream error:",
                e.response.content.decode(e.response.encoding or "utf-8", errors="replace"),
            )
    except Exception as e:
        print("Error:", e)
        raise


def load_config(configuration_file: str) -> dict | None:
    """
    Load a configuration file and return its contents as a dict.

    Args:
        configuration_file: Path to the JSON configuration file.

    Returns:
        Parsed config dict, or None if the file is not found.
    """
    logging.debug("Loading config from %s...", configuration_file)
    try:
        with open(configuration_file) as file:
            loaded = json.load(file)
        logging.debug("Config loaded successfully.")
        return loaded
    except FileNotFoundError:
        logging.debug("No configuration file %s found.", configuration_file)
        return None


def main() -> None:
    global config, local_config, client

    parameters = docopt(__doc__, version=f"thingiverse-publisher {__version__}")

    if parameters["--verbose"]:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)

    base = load_config(os.path.expanduser("~/.thingiverse_publisher.json"))
    if base:
        config.update(base)
    local = load_config(".thingiverse_publisher.json")
    if local:
        local_config = local
        config.update(local)

    if parameters["--bearer-token"]:
        config["bearer_token"] = parameters["--bearer-token"]
    if parameters["--username"]:
        config["username"] = parameters["--username"]

    with open("README.md", "rb") as file:
        config["thing"]["description"] = file.read().decode("utf-8")
    with open("print-instructions.md", "rb") as file:
        config["thing"]["instructions"] = file.read().decode("utf-8")

    client = AuthenticatedClient(
        base_url=BASE_URL_PRODUCTION,
        token=config["bearer_token"],
    )

    create_or_update_thing()
    logging.info("Saving config...")
    local_config["thing"].pop("description")
    local_config["thing"].pop("instructions")
    with open(".thingiverse_publisher.json", "w") as file:
        json.dump(local_config, file, indent=2)


if __name__ == "__main__":
    main()
