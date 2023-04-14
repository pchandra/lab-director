import json
import subprocess
from taskdef import *

KEYBPM_BIN = '/Users/chandra/ll/co/key-bpm-finder/keymaster-json.py'

def execute(filename, status):
    # Build the command line to run
    cmdline = []
    cmdline.append('/usr/local/bin/python3.9')
    cmdline.append(KEYBPM_BIN)
    cmdline.append(filename)
    # Execute the command
    process = subprocess.Popen(cmdline, 
                               stdout=subprocess.PIPE,
                               universal_newlines=True)
    stdout, _ = process.communicate()
    # The tool outputs JSON so return it as a dict
    return json.loads(stdout)
