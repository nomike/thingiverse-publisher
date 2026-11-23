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
  "bearer_token": "123456789abcdef123456789abcdef12"
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
    "license": "gpl3",
  },
  "files": [
    "i3-ptfe-tube-cutting-measure.scad",
    "i3-ptfe-tube-cutting-measure.stl"
  ],
  "images": []
}
```

### Available license options

Thingiverse currently does not document which licenses you can use in the API.
This interface does not seem to be symetric though. What you get as a value for "license" in a response, is not accepted as a value in a request. I've created a support case for getting a list of valid options with thingiverse, and I'm currently waiting for a response.

Valid options I have found so far are:

cc: Creative Commons - Attribution

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
