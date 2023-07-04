import subprocess
from taskdef import *
import taskapi as api
from . import helpers
from . import filestore
from config import CONFIG as conf

FFMPEG_BIN = conf['FFMPEG_BIN']
FILESTORE_SCRATCH = conf['FILESTORE_SCRATCH']
FILESTORE_PURCHASES = conf['FILESTORE_PURCHASES']

def export(file_id, key, fmt):
    private, public = helpers.get_bucketnames(file_id)
    status = api.get_status(file_id)

    # Screen for formats we'll support
    if not fmt in [ 'mp3', 'aiff', 'flac', 'ogg', 'wav' ]:
        return False, f"EXPT: format {fmt} isn't accepted for {key}"

    # Short-circuit if the filestore already has assets we would produce
    output_keys = [ f"{key}.{fmt}" ]
    if filestore.check_keys(file_id, output_keys, FILESTORE_SCRATCH):
        return True, f"EXPT: {key}.{fmt} already exists for {file_id}"


    scratch = helpers.create_scratch_dir()
    try:
        infile = filestore.retrieve_file(file_id, f"{key}.wav", scratch, private)
    except:
        helpers.destroy_scratch_dir(scratch)
        return False, f"EXPT: file {key}.wav isn't found for {file_id}"

    # Special case for WAV requests
    if fmt == 'wav':
        outfile = infile
    else:
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

    filestore.store_file(file_id, outfile, f"{key}.{fmt}", FILESTORE_SCRATCH)
    helpers.destroy_scratch_dir(scratch)
    return True, f"EXPT: {key}.{fmt} successfully created for {file_id}"
