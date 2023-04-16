import subprocess
from taskdef import *
from . import helpers
from . import filestore
from config import CONFIG as conf

FFMPEG_BIN = conf['FFMPEG_BIN']

def execute(file_id, status, force=False):
    # Short-circuit if the filestore already has assets we would produce
    output_keys = [ f"{Tasks.ORIG.value}", f"{Tasks.ORIG.value}.mp3" ]
    if not force and filestore.check_keys(file_id, status, output_keys):
        return

    # Proceed with running this task
    ret = {}
    # Special case call with None to bootstrap
    local_file = filestore.retrieve_file(file_id, status, None, helpers.WORK_DIR + f"/{status['uuid']}")
    ret['output'] = filestore.store_file(file_id, status, local_file, f"{Tasks.ORIG.value}")

    # Run FFMPEG to make MP3 version
    outfile = f"{helpers.WORK_DIR}/{status['uuid']}-{Tasks.ORIG.value}.mp3"
    # Run an FFMPEG cmd to detect silence
    cmdline = []
    cmdline.append(FFMPEG_BIN)
    cmdline.extend([ "-i", local_file,
                     "-b:a", "320k",
                     "-y"
                   ])
    cmdline.append(outfile)
    process = subprocess.Popen(cmdline,
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               universal_newlines=True)
    stdout, stderr = process.communicate(input="\n\n\n\n\n")

    # Store the resulting file
    ret['mp3'] = filestore.store_file(file_id, status, outfile, f"{Tasks.ORIG.value}.mp3")

    # Build the dict to return to caller
    ret["command"] = { "stdout": stdout, "stderr": stderr }
    return ret
