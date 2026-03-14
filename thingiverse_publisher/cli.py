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

The script uses the 'docopt' library to parse command-line arguments and the 'requests' library to make HTTP requests.
"""

import json
import logging
import os
from datetime import datetime

import requests
from docopt import docopt

from thingiverse_publisher import __version__

local_config: dict = {}
config: dict = {}
headers: dict = {}
api_base_url: str = ""


def check_file_mtime(file_path: str, type: str) -> bool:
    global config, headers, api_base_url

    local_mtime = datetime.fromtimestamp(os.path.getmtime(file_path)).astimezone()
    # Send an API request to get metadata of the image
    response = requests.get(
        f"{api_base_url}/THINGS/{config['thing']['id']}/{type.upper()}S/{config[f'{type}s'][file_path]['id']}",
        headers=headers,
    )
    logging.debug("Response status code: %s", response.status_code)
    logging.debug("Response data: %s", json.dumps(response.json(), indent=2))
    response.raise_for_status()  # Raise an error if the request failed
    if type == "file":
        thingiverse_mtime = datetime.fromisoformat(response.json()["date"] + "Z")
    elif type == "image":
        thingiverse_mtime = datetime.fromisoformat(response.json()["added"])
    else:
        raise ValueError(f"Unknown type: {type}")
    logging.debug("Local mtime: %s", local_mtime)
    logging.debug("Thingiverse mtime: %s", thingiverse_mtime.astimezone())
    return local_mtime > thingiverse_mtime


def upload_image_or_file(file_path: str, type: str) -> None:
    global config, headers, api_base_url, local_config
    if "id" in local_config[f"{type}s"][file_path]:
        if check_file_mtime(file_path, type):
            logging.info(
                "Local %s is newer than the one on Thingiverse. Deleting old %s...",
                type,
                type,
            )
            response = requests.delete(
                f"{api_base_url}/THINGS/{config['thing']['id']}/{type.upper()}S/{config[f'{type}s'][file_path]['id']}",
                headers=headers,
            )
            logging.debug("Response status code: %s", response.status_code)
            logging.debug("Response data: %s", json.dumps(response.json(), indent=2))
            response.raise_for_status()
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
    prepare_response = requests.post(
        f"{api_base_url}/THINGS/{config['thing']['id']}/FILES",
        headers=headers,
        json={"filename": os.path.basename(file_path)},
    )
    logging.debug("Response status code: %s", prepare_response.status_code)
    logging.debug("Response data: %s", json.dumps(prepare_response.json(), indent=2))
    prepare_response.raise_for_status()  # Raise an error if the request failed
    logging.info("File upload requested.")

    logging.info("Uploading %s %s...", type, file_path)
    with open(file_path, "rb") as file:
        upload_response = requests.post(
            prepare_response.json()["action"],
            files={"file": file},
            data=prepare_response.json()["fields"],
        )
    logging.debug("Response status code: %s", upload_response.status_code)
    logging.debug("Response data: %s", json.dumps(upload_response.json(), indent=2))
    upload_response.raise_for_status()  # Raise an error if the request failed
    logging.info("%s uploaded successfully!", type.capitalize())
    logging.info("Calling finalizer...")
    response = requests.post(
        prepare_response.json()["fields"]["success_action_redirect"],
        headers=headers,
        data=prepare_response.json()["fields"],
    )
    logging.debug("Response status code: %s", response.status_code)
    logging.debug("Response data: %s", json.dumps(response.json(), indent=2))
    local_config[f"{type}s"][file_path] = response.json()


def upload_image(image_path: str) -> None:
    upload_image_or_file(image_path, "image")


def upload_file(file_path: str) -> None:
    upload_image_or_file(file_path, "file")


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
    global local_config, config, headers, api_base_url

    try:
        if "id" not in config["thing"]:
            logging.info("No ID found in config. Checking if thing already exists...")
            logging.debug("List all things owned by %s...", config["username"])
            response = requests.get(
                f"{api_base_url}/USERS/{config['username']}/THINGS",
                headers=headers,
            )
            response.raise_for_status()  # Raise an error if the request failed
            data = response.json()
            logging.debug("Response status code: %s", response.status_code)
            logging.debug("Response data: %s", json.dumps(data, indent=2))

            matching_things = [thing for thing in data if thing["name"] == config["thing"]["name"]]
            if len(matching_things) > 1:
                raise ValueError(
                    f"More than one thing with name {config['thing']['name']} found. Please delete all but one."
                )
            if len(matching_things) == 1:
                logging.info(
                    "Thing with name %s already exists. Using id %s.",
                    config["thing"]["name"],
                    matching_things[0]["id"],
                )
                local_config["thing"]["id"] = matching_things[0]["id"]
                config["thing"]["id"] = matching_things[0]["id"]
            else:
                logging.info(
                    "No thing with name %s found. New thing will be created.",
                    config["thing"]["name"],
                )
        if "id" not in config["thing"]:
            logging.info("Thing does not exist, creating a new one...")
            response = requests.post(
                f"{api_base_url}/THINGS",
                headers=headers,
                json=config["thing"],
            )
            response.raise_for_status()  # Raise an error if the request failed
            logging.info("Thing created successfully!")
            logging.debug("Response status code: %s", response.status_code)
            logging.debug("Response data: %s", json.dumps(response.json(), indent=2))
            config["thing"]["id"] = response.json()["id"]
        else:
            logging.info(
                "Thing does exist. Patching existing thing with ID %s...",
                config["thing"]["id"],
            )
            response = requests.patch(
                f"{api_base_url}/things/{config['thing']['id']}",
                headers=headers,
                json=config["thing"],
            )
            response.raise_for_status()  # Raise an error if the request failed
            logging.info("Thing patched successfully!")
            logging.debug("Response status code: %s", response.status_code)
            logging.debug("Response data: %s", json.dumps(response.json(), indent=2))

        logging.info("Uploading files...")
        for file in config["files"]:
            upload_file(file)
        logging.info("Uploading images...")
        for file in config["images"]:
            upload_image(file)

    except requests.exceptions.RequestException as e:
        print("Error:", e)
        if e.response is not None:
            print(
                "Upstream error:",
                e.response.content.decode(e.response.encoding or "utf-8", errors="replace"),
            )


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
    global config, local_config, headers, api_base_url

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

    api_base_url = "https://api.thingiverse.com"

    headers = {
        "Authorization": f"Bearer {config['bearer_token']}",
        "Host": "api.thingiverse.com",
        "Content-Type": "application/json; charset=utf-8",
    }

    create_or_update_thing()
    logging.info("Saving config...")
    local_config["thing"].pop("description")
    local_config["thing"].pop("instructions")
    with open(".thingiverse_publisher.json", "w") as file:
        json.dump(local_config, file, indent=2)


if __name__ == "__main__":
    main()
