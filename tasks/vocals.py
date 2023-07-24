import json
import subprocess
from taskdef import *
from . import helpers
from . import filestore
from config import CONFIG as conf

GENRE_BIN = conf['GENRE_BIN']

def execute(tg, force=False):
    # Short-circuit if the filestore already has assets we would produce
    tg.add_public([ f"{Tasks.VOCL.value}.json" ])
    if not force and tg.check_keys():
        return True, helpers.msg('Already done')

    # Get the stem metadata from the filestore
    stem_json = tg.get_file(f"{Tasks.STEM.value}.json")
    if stem_json is None:
        return False, helpers.msg(f'Input file not found: {Tasks.STEM.value}.json')
    metadata = None
    with open(stem_json, 'r') as f:
        metadata = json.load(f)

    output = {}
    output['instrumental'] = metadata['instrumental']
    output['vocals'] = {}
    # Do the work if it isn't an instrumental
    if not metadata['instrumental']:
        filename = tg.get_file(f"{Tasks.STEM.value}-vocals.mp3")
        if filename is None:
            return False, helpers.msg(f'Input file not found: {Tasks.STEM.value}-vocals.mp3')
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

    tempfile = f"{tg.scratch}/{Tasks.VOCL.value}.json"
    with open(tempfile, 'w') as f:
        f.write(json.dumps(output, indent=2))
    stored_location = tg.put_file(tempfile, f"{Tasks.VOCL.value}.json")
    # The tool outputs JSON so return it as a dict
    ret = {}
    ret['data'] = output
    ret['output'] = stored_location
    return True, ret
