# Thingiverse Publisher

A small tool for publishig things to Thingiverse.

The tool is very rudimentary and needs some code-clenup, but it does it's job, which is to upload a 3D model to Thingiverse.
It is in a very early stage of development, so expect breaking changes.

## Pre-requisites

- Python 3.10 or later
- A Thingiverse account
- A Thingiverse Bearer token

## Installing

From the project directory:

```bash
pip install .
```

For an editable install (development):

```bash
pip install -e .
```

This installs the `thingiverse-publisher` command on your PATH.

## Configuring

Place a file `.thingiverse_publisher.json` in your home directory with the following content (see below on how to get a bearer token):

```json
{
  "bearer_token": "123456789abcdef123456789abcdef12",
  "username": "nomike"
}
```

Place a file `.thingiverse_publisher.json` in the directory of your 3D model. The file should look like this:

```json
{
  "thing": {
    "name": "i3 PTFE tube cutting measure",
    "category": "Art",
    "tags": [
      "foo",
      "bar",
      "baz"
    ],
    "instructions": "Print and enjoy",
    "is_wip": true,
    "license": "gpl"
  },
  "files": {
    "i3-ptfe-tube-cutting-measure.scad": {},
    "i3-ptfe-tube-cutting-measure.stl": {}
  },
  "images": {
    "photos/preview.jpg": {}
  }
}
```

`files` and `images` are objects keyed by the local path. The tool stores the Thingiverse ID of each uploaded
file/image in the (initially empty) entry and rewrites `.thingiverse_publisher.json` after each run, so the
next run only re-uploads files that changed. The same applies to `thing.id`, which is added after the thing
has been created. If a run fails part-way, the config is still saved (so IDs of things already created are
kept) and the tool exits with a non-zero status.

### Available license options

The `license` value must be one of these codes (the tool stops with an error for anything else, instead of
silently picking a different license). The Thingiverse display name, e.g. `BSD License`, is also accepted.
If `license` is omitted, new things are created with `cc`.

| Code       | License                                                  |
| ---------- | -------------------------------------------------------- |
| `cc`       | Creative Commons - Attribution                           |
| `cc-sa`    | Creative Commons - Attribution - Share Alike             |
| `cc-nd`    | Creative Commons - Attribution - No Derivatives          |
| `cc-nc-sa` | Creative Commons - Attribution - Non-Commercial - Share Alike |
| `cc-nc-nd` | Creative Commons - Attribution - Non-Commercial - No Derivatives |
| `pd0`      | Public Domain                                            |
| `gpl`      | GNU - GPL                                                |
| `lgpl`     | GNU - LGPL                                               |
| `bsd`      | BSD License                                              |

## Getting a Bearer Token

1. Go to <https://www.thingiverse.com/apps/create>
1. Fill in the form. Set the **Callback URL** to `http://127.0.0.1:12345/`
1. Click on "Create Application"
1. Copy the "Client ID" to a safe place
1. Make sure you are logged into Thingiverse, then open:

   `https://www.thingiverse.com/login/oauth/authorize?client_id=YOUR_CLIENT_ID&redirect_uri=http://127.0.0.1:12345/&response_type=token`

1. Click on "Allow"
1. Your browser will try to open `http://127.0.0.1:12345/`. The page will not load
   (nothing is listening there); that is expected. Look at the address bar: the URL
   contains `#access_token=...`. Copy the token value (everything after
   `access_token=` up to the next `&`, if any).
1. Put that token into your `~/.thingiverse_publisher.json` file as `bearer_token`
