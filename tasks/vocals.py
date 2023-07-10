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
    public_keys = [ f"{Tasks.VOCL.value}.json" ]
    output_keys = [ ] + public_keys
    if not force and filestore.check_keys(file_id, output_keys, private):
        if not filestore.check_keys(file_id, public_keys, public):
            filestore.copy_keys(file_id, public_keys, private, public)
        helpers.destroy_scratch_dir(scratch)
        return

    # Get the stem metadata from the filestore
    stem_json = filestore.retrieve_file(file_id, f"{Tasks.STEM.value}.json", scratch, private)
    metadata = None
    with open(stem_json, 'r') as f:
        metadata = json.load(f)

    output = {}
    output['instrumental'] = metadata['instrumental']
    output['vocals'] = {}
    # Do the work if it isn't an instrumental
    if not metadata['instrumental']:
        filename = filestore.retrieve_file(file_id, f"{Tasks.STEM.value}-vocals.mp3", scratch, private)
        # Chomp all silence from the file
        trimfile = helpers.make_nonsilent_wave(filename)

        # Run both through the vocal detection tool
        for name, file in [('full', filename), ('trim', trimfile)]:
            # Build the command line to run
            cmdline = []
            cmdline.append(GENRE_BIN)
            cmdline.append('vocals')
            cmdline.append(file)
            # Execute the command
            process = subprocess.Popen(cmdline,
                                       stdout=subprocess.PIPE,
                                       universal_newlines=True)
            stdout, _ = process.communicate()
            # Load JSON object
            output['vocals'][name] = json.loads(stdout)
        output['duration'] = { 'full': helpers.get_duration(filename),
                               'trim': helpers.get_duration(trimfile) }

    tempfile = f"{scratch}/{Tasks.VOCL.value}.json"
    with open(tempfile, 'w') as f:
        f.write(json.dumps(output, indent=2))
    stored_location = filestore.store_file(file_id, tempfile, f"{Tasks.VOCL.value}.json", private)
    # The tool outputs JSON so return it as a dict
    ret = {}
    ret['data'] = output
    ret['output'] = stored_location
    filestore.copy_keys(file_id, public_keys, private, public)
    helpers.destroy_scratch_dir(scratch)
    return ret
