import json
import subprocess
from taskdef import *
from . import helpers
from config import CONFIG as conf

GENRE_BIN = conf['GENRE_BIN']

def execute(tg, force=False):
    if tg.status['type'] not in [ 'beat', 'song' ]:
        return False, helpers.msg('Track is not a beat or song')
    # Short-circuit if the filestore already has assets we would produce
    tg.add_public([ f"{Tasks.GENR.value}.json" ])
    if not force and tg.check_keys():
        return True, helpers.msg('Already done')

    # Use the WAV of the original for analysis
    filename = tg.get_file(f"{Tasks.ORIG.value}.mp3")
    if filename is None:
        return False, helpers.msg(f'Input file not found: {Tasks.ORIG.value}.mp3')
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

    tempfile = f"{tg.scratch}/{Tasks.GENR.value}.json"
    with open(tempfile, 'w') as f:
        f.write(json.dumps(output, indent=2))
    stored_location = tg.put_file(tempfile, f"{Tasks.GENR.value}.json")
    # The tool outputs JSON so return it as a dict
    ret = {}
    ret['data'] = output
    ret['output'] = stored_location
    return True, ret
