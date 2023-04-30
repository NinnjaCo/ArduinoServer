import http.server
import itertools
import logging
import platform
import os
import subprocess
import tempfile
from fastapi import FastAPI, Body, HTTPException
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware
import uvicorn
from typing import Annotated

app = FastAPI()

origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_headers=["*"],
    allow_methods=["*"],
)



logging.basicConfig(level=logging.DEBUG)
arduino_cmd = None

@app.get('/')
async def root():
    return {'status': '200'}


class Code(BaseModel):
    code: str

@app.post('/upload')
async def upload(code: Code):
    actual_code = code.code

    portname = guess_port_name()
    if not portname:
        raise HTTPException(status_code=500, detail="Make sure arduino is connected")

    cmd = get_arduino_command()
    if not cmd:
        raise HTTPException(status_code=501, detail="Couldn't find Arduino command")
    
    dirname = tempfile.mkdtemp()
    sketchname = os.path.join(dirname, os.path.basename(dirname)) + ".ino"
    f = open(sketchname, "wb")
    f.write(actual_code.encode("utf-8") + b"\n")
    f.close()

    cmd_line = [cmd, "--upload", "--port", portname]
    cmd_line.append(sketchname)
    logging.debug("Running: %s", " ".join(cmd_line))

    rc = subprocess.call(cmd_line)
    if rc != 0:
        print("Arduino command failed:" + rc)
        raise HTTPException(status_code=400, detail="Arduino command failed")

    return {'status': '200', 'message': "OK"}

def get_arduino_command():
    """Attempt to find or guess the path to the Arduino binary."""
    global arduino_cmd
    if not arduino_cmd:
        if platform.system() == "Darwin":
            arduino_cmd_guesses = ["/Applications/Arduino.app/Contents/MacOS/Arduino"]
        elif platform.system() == "Windows":
            arduino_cmd_guesses = [
                "c:\Program Files\Arduino\Arduino_debug.exe",
                "c:\Program Files (x86)\Arduino\Arduino_debug.exe",
                "c:\Program Files\Arduino\Arduino.exe",
                "c:\Program Files (x86)\Arduino\Arduino.exe",
            ]
        else:
            arduino_cmd_guesses = []

        for guess in arduino_cmd_guesses:
            if os.path.exists(guess):
                logging.info("Found Arduino command at %s", guess)
                arduino_cmd = guess
                break
        else:
            logging.info("Couldn't find Arduino command; hoping it's on the path!")
            arduino_cmd = "arduino"
    return arduino_cmd

def guess_port_name():
    """Attempt to guess a port name that we might find an Arduino on."""
    portname = None
    if platform.system() == "Windows":
        import winreg
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, "HARDWARE\\DEVICEMAP\\SERIALCOMM")
        # We'll guess it's the last COM port.
        for i in itertools.count():
            try:
                portname = winreg.EnumValue(key, i)[1]
            except WindowsError:
                break
    else:
        # We'll guess it's the first non-bluetooth tty. or cu. prefixed device
        ttys = [filename for filename in os.listdir("/dev")
                if (filename.startswith("tty.") or filename.startswith("cu."))
                and not "luetooth" in filename]
        ttys.sort(key=lambda k:(k.startswith("cu."), k))
        if ttys:
            portname = "/dev/" + ttys[0]
    logging.info("Guessing port name as %s", portname)
    return portname


if __name__ == '__main__':
     uvicorn.run(app, port=8080, log_level="info")
