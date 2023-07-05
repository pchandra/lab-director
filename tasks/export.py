import os
import subprocess
from taskdef import *
import taskapi as api
from . import helpers
from . import filestore
from config import CONFIG as conf

FFMPEG_BIN = conf['FFMPEG_BIN']
FILESTORE_SCRATCH = conf['FILESTORE_SCRATCH']
FILESTORE_PURCHASES = conf['FILESTORE_PURCHASES']

def _tag(msg):
    return f"{os.path.basename(__file__)}: {msg}"

def export(file_id, key, fmt):
    private, public = helpers.get_bucketnames(file_id)
    status = api.get_status(file_id)

    if status['type'] in [ 'beat', 'song' ]:
        # Lots of sanity and error checking first
        special = [ 'all', 'purchase-mp3', 'purchase-wav', 'purchase-stem' ]
        if key in special:
            formats = [ 'zip', 'tgz' ]
        else:
            formats = [ 'mp3', 'aiff', 'flac', 'ogg', 'wav' ]

        # Screen acceptable input we support
        if not fmt in formats:
            return False, _tag(f"format {fmt} isn't accepted for {key}")

        # Short-circuit on format conversion if the filestore already has it
        output_keys = [ f"{key}.{fmt}" ]
        if key not in special and filestore.check_keys(file_id, output_keys, FILESTORE_SCRATCH):
            return True, _tag(f"{key}.{fmt} already exists for {file_id}")

        # Ok, we're going to have to do some work
        scratch = helpers.create_scratch_dir()

        # Do special cases
        if key == 'all':
            helpers.destroy_scratch_dir(scratch)
            return True, _tag("stub")
        elif key =='purchase-mp3':
            helpers.destroy_scratch_dir(scratch)
            return True, _tag("stub")
        elif key =='purchase-wav':
            helpers.destroy_scratch_dir(scratch)
            return True, _tag("stub")
        elif key =='purchase-stem':
            helpers.destroy_scratch_dir(scratch)
            return True, _tag("stub")

        try:
            infile = filestore.retrieve_file(file_id, f"{key}.wav", scratch, private)
        except:
            helpers.destroy_scratch_dir(scratch)
            return False, _tag(f"file {key}.wav isn't found for {file_id}")

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
        return True, _tag(f"{key}.{fmt} successfully created for {file_id}")
    elif status['type'] == 'soundkit':
        return True, _tag("stub")

    return False, _tag(f"request {fmt} isn't accepted for {key}")
