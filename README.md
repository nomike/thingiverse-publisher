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
1. Fill in the form
1. Click on "Create Application"
1. Copy the "Client ID" and "Client Secret" to a safe place
1. Open a browser and go to `https://www.thingiverse.com/login/oauth/authorize?client_id=YOUR_CLIENT_ID&redirect_uri=urn:ietf:wg:oauth:2.0:oob&response_type=code`
1. Click on "Allow"
1. Copy the code from the address bar
1. Open a terminal and run the following command:

```bash
curl -X POST -d "client_id=YOUR_CLIENT_ID&client_secret=YOUR_CLIENT_SECRET&code=YOUR_CODE&grant_type=authorization_code" https://www.thingiverse.com/login/oauth/access_token
```

1. Copy the `access_token` to your `.thingiverse_publisher.json` file
