import subprocess
from taskdef import *
from . import helpers
from . import filestore
from config import CONFIG as conf

FFMPEG_BIN = conf['FFMPEG_BIN']
FILESTORE_SCRATCH = conf['FILESTORE_SCRATCH']

def convert(file_id, out_id, key, fmt):
    private, public = helpers.get_bucketnames(file_id)
    status = api.get_status(file_id)

    if not key in [ 'mp3', 'aiff', 'flac', 'ogg']
    scratch = helpers.create_scratch_dir()
    infile = filestore.retrieve_file(file_id, f"{key}.wav", scratch, private)
    outfile = f"{scratch}/{key}.{fmt}"

    # #execute the command
    cmdline = []
    cmdline.append(FFMPEG_BIN)
    cmdline.extend([ "-i", infile,
                     "-v", "quiet",
                     "-y"
                   ])
    if key == 'mp3' or key == 'ogg':
        cmdline.append("-b:a", "320k")
    cmdline.append(outfile)
    process = subprocess.Popen(cmdline,
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               universal_newlines=True)
    stdout, stderr = process.communicate(input="\n\n\n\n\n")

    filestore.store_file(file_id, outfile, f"{out_id}/{key}.{fmt}", FILESTORE_SCRATCH)
    helpers.destroy_scratch_dir(scratch)
