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
    output_keys = [ f"{Tasks.VOCL.value}.json" ]
    if not force and filestore.check_keys(file_id, output_keys, public):
        return

    # Proceed with running this task
    scratch = helpers.create_scratch_dir()

    # Get the stem metadata from the filestore
    stem_json = filestore.retrieve_file(file_id, f"{Tasks.STEM.value}.json", scratch, public)
    metadata = None
    with open(stem_json, 'r') as f:
        metadata = json.load(f)

    output = {}
    output['instrumental'] = metadata['instrumental']
    output['vocals'] = {}
    # Do the work if it isn't an instrumental
    if not metadata['instrumental']:
        filename = filestore.retrieve_file(file_id, f"{Tasks.ORIG.value}.mp3", scratch, private)
        # Build the command line to run
        cmdline = []
        cmdline.append(GENRE_BIN)
        cmdline.append('vocals')
        cmdline.append(filename)
        # Execute the command
        process = subprocess.Popen(cmdline,
                                   stdout=subprocess.PIPE,
                                   universal_newlines=True)
        stdout, _ = process.communicate()
        # Load JSON object
        output['vocals'] = json.loads(stdout)

    tempfile = f"{scratch}/{Tasks.VOCL.value}.json"
    with open(tempfile, 'w') as f:
        f.write(json.dumps(output, indent=2))
    stored_location = filestore.store_file(file_id, tempfile, f"{Tasks.VOCL.value}.json", public)
    # The tool outputs JSON so return it as a dict
    ret = {}
    ret['data'] = output
    ret['output'] = stored_location
    helpers.destroy_scratch_dir(scratch)
    return ret
