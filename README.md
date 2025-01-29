# Thingiverse Publisher

A small tool for publishig things to Thingiverse.

The tool is very rudimentary and needs some code-clenup, but it does it's job, which is to upload a 3D model to Thingiverse.
It is in a very early stage of development, so expect breaking changes.

## Pre-requisites

- Python 3.6 or later
- python3-docopt
- python3-requests
- A Thingiverse account
- A Thingiverse Bearer token

## Installing

```bash
sudo make install
```

## Uninstalling

```bash
sudo make uninstall
```

## Configuring

Place a file `.thingiverse_publisher.jso` in your home directory with the following content (see below on how to get a bearer token):

```json
{
  "bearer_token": "123456789abcdef123456789abcdef12"
  "username": "nomike"
}
```

Place a file `.thingiverse_publisher.jso` in the directory of your 3D model. The file should look like this:

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

Thingiverse currently does not document which licenses you can use in the API. Since the move to the new API though, the option could be set to any string availbable in the web GUI.
These currently are:

- Create Commons - Attribution
- Create Commons - Attribution - Share Alike
- Create Commons - Attribution - No Derivatives
- Create Commons - Attribution - Non-Commercial
- Create Commons - Attribution - Non-Commercial - Share Alike
- Create Commons - Attribution - Non-Commercial - No Derivatives
- Create Commons - Public Domain Dedication
- GNU - GPL
- GNU - LGPL
- BSD License

## Getting a Bearer Token

1. Go to <https://www.thingiverse.com/apps/create>
2. Fill in the form
3. Click on "Create Application"
4. Copy the "Client ID" and "Client Secret" to a safe place
5. Open a browser and go to `https://www.thingiverse.com/login/oauth/authorize?client_id=YOUR_CLIENT_ID&redirect_uri=urn:ietf:wg:oauth:2.0:oob&response_type=code`
6. Click on "Allow"
7. Copy the code from the address bar
8. Open a terminal and run the following command:

```bash
curl -X POST -d "client_id=YOUR_CLIENT_ID&client_secret=YOUR_CLIENT_SECRET&code=YOUR_CODE&grant_type=authorization_code" https://www.thingiverse.com/login/oauth/access_token
```

9. Copy the `access_token` to your `.thingiverse_publisher.json` file
