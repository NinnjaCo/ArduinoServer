# Arduino Server

## Description

This is a simple server that can be downloaded as an executable and run on a computer. It will listen for post requests to upload the code to the arduino.

## Usage

1. Download the executable from the releases page
2. Run the executable
3. Send a post request to the server with the code in the body of the request
4. The server will upload the code to the arduino

## How to build the executable

```pyinstaller --onefile --windowed main.py```
This will create an executable in the dist folder
this executable can be run on any computer without python installed
by simply double clicking on it

## How to run the server

1. ```pip install -r requirements.txt```
2. ```python main.py```

## Sending a post request

In the post request body, add:

```json
{
    "code": "code here"
}
```

## License

Licensed under the [MIT License](LICENSE)
