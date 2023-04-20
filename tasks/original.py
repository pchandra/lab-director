import subprocess
import taglib
from taskdef import *
from . import helpers
from . import filestore
from config import CONFIG as conf

FFMPEG_BIN = conf['FFMPEG_BIN']

def execute(file_id, force=False):
    # Short-circuit if the filestore already has assets we would produce
    output_keys = [ f"{Tasks.ORIG.value}", f"{Tasks.ORIG.value}.mp3" ]
    if not force and filestore.check_keys(file_id, output_keys):
        return

    # Proceed with running this task
    ret = {}
    scratch = helpers.create_scratch_dir()
    # Get the external file
    local_file = filestore.get_external_file(file_id, scratch)
    # Strip any tags it might have in it
    with taglib.File(local_file, save_on_exit=True) as beat:
        beat.removeUnsupportedProperties(beat.unsupported)
    with taglib.File(local_file, save_on_exit=True) as beat:
        tags = []
        for tag in beat.tags.keys():
            tags.append(str(tag))
        for tag in tags:
            del beat.tags[tag]
    # Save it as the original to the filestore
    ret['output'] = filestore.store_file(file_id, local_file, f"{Tasks.ORIG.value}")

    # Run FFMPEG to make MP3 version
    outfile = f"{scratch}/{Tasks.ORIG.value}.mp3"
    # Run an FFMPEG cmd to compress to mp3
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
    ret['mp3'] = filestore.store_file(file_id, outfile, f"{Tasks.ORIG.value}.mp3")

    # Build the dict to return to caller
    ret["command"] = { "stdout": stdout, "stderr": stderr }
    helpers.destroy_scratch_dir(scratch)
    return ret
