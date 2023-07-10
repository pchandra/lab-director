import json
import subprocess
from taskdef import *
from . import helpers
from . import filestore
from config import CONFIG as conf

GENRE_BIN = conf['GENRE_BIN']

def execute(file_id, force=False):
    private, public = helpers.get_bucketnames(file_id)
    scratch = helpers.create_scratch_dir()
    # Short-circuit if the filestore already has assets we would produce
    public_keys = [ f"{Tasks.GENR.value}.json" ]
    output_keys = [ ] + public_keys
    if not force and filestore.check_keys(file_id, output_keys, private):
        if not filestore.check_keys(file_id, public_keys, public):
            filestore.copy_keys(file_id, public_keys, private, public)
        helpers.destroy_scratch_dir(scratch)
        return True, helpers.msg('Already done')

    # Use the WAV of the original for analysis
    try:
        filename = filestore.retrieve_file(file_id, f"{Tasks.ORIG.value}.mp3", scratch, private)
    except:
        helpers.destroy_scratch_dir(scratch)
        return False, helpers.msg(f'Input file(s) not found')
    genres = [ 'core', 'mood', 'blues', 'classical', 'country', 'electronic', 'hiphop', 'jazz', 'metal', 'reggae', 'rock']
    output = {}
    for g in genres:
        # Build the command line to run
        cmdline = []
        cmdline.append(GENRE_BIN)
        cmdline.append(g)
        cmdline.append(filename)
        # Execute the command
        process = subprocess.Popen(cmdline,
                                   stdout=subprocess.PIPE,
                                   universal_newlines=True)
        stdout, _ = process.communicate()
        # Load JSON object
        output[g] = json.loads(stdout)

    tempfile = f"{scratch}/{Tasks.GENR.value}.json"
    with open(tempfile, 'w') as f:
        f.write(json.dumps(output, indent=2))
    stored_location = filestore.store_file(file_id, tempfile, f"{Tasks.GENR.value}.json", private)
    # The tool outputs JSON so return it as a dict
    ret = {}
    ret['data'] = output
    ret['output'] = stored_location
    filestore.copy_keys(file_id, public_keys, private, public)
    helpers.destroy_scratch_dir(scratch)
    return True, ret
