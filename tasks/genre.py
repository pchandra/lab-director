import json
import subprocess
from taskdef import *
from . import helpers
from . import filestore
from config import CONFIG as conf

GENRE_BIN = conf['GENRE_BIN']

def execute(file_id, force=False):
    private, public = helpers.get_bucketnames(file_id)
    # Short-circuit if the filestore already has assets we would produce
    output_keys = [ f"{Tasks.GENR.value}.json" ]
    if not force and filestore.check_keys(file_id, output_keys, public):
        return

    # Proceed with running this task
    scratch = helpers.create_scratch_dir()
    filename = filestore.retrieve_file(file_id, f"{Tasks.ORIG.value}.wav", scratch, private)
    genres = [ 'core', 'blues', 'classical', 'country', 'electronic', 'hiphop', 'jazz', 'metal', 'reggae', 'rock']
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
    stored_location = filestore.store_file(file_id, tempfile, f"{Tasks.GENR.value}.json", public)
    # The tool outputs JSON so return it as a dict
    ret = {}
    ret['data'] = output
    ret['output'] = stored_location
    helpers.destroy_scratch_dir(scratch)
    return ret
