# CurlPythonServer

<img align="top" alt="ferris the crab snapping hearts" width="350" src="https://cdn.dribbble.com/users/1579739/screenshots/19716716/media/4ec319c00b1f61ba3ed77c0ee22359e7.gif"/>

## Pilot:
This app is a python automation for serving and uploading files on a host

## Usage:

### start the server:

`python3 app.py`

### UI upload:
Visit `http://<ip/localhost>:8000` to view and upload files.

### CLI upload:
The server also supports manual CLI upload through `curl` post capabilities.

use:

`curl -F file=@path_to_your_file http://<ip/localhost>:8000`

for uploads
