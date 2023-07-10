import re
import json
import subprocess
from taskdef import *
from . import helpers
from . import filestore
from config import CONFIG as conf

FFMPEG_BIN = conf['FFMPEG_BIN']
PHASELIMITER_BIN = conf['PHASELIMITER_BIN']

def execute(file_id, force=False):
    private, public = helpers.get_bucketnames(file_id)
    scratch = helpers.create_scratch_dir()
    # Short-circuit if the filestore already has assets we would produce
    public_keys = [ ]
    output_keys = [ f"{Tasks.MAST.value}.wav",
                    f"{Tasks.MAST.value}.mp3" ] + public_keys
    if not force and filestore.check_keys(file_id, output_keys, private):
        if not filestore.check_keys(file_id, public_keys, public):
            filestore.copy_keys(file_id, public_keys, private, public)
        helpers.destroy_scratch_dir(scratch)
        return True, helpers.msg('Already done')

    try:
        filename = filestore.retrieve_file(file_id, f"{Tasks.ORIG.value}.wav", scratch, private)
    except:
        helpers.destroy_scratch_dir(scratch)
        return False, helpers.msg(f'Input file(s) not found')
    outfile = f"{scratch}/{Tasks.MAST.value}.wav"

    # Get the info for the original file to get the bit depth
    infofile = filestore.retrieve_file(file_id, f"{Tasks.ORIG.value}.json", scratch, private)
    with open(infofile, 'r') as f:
        info = json.load(f)
    bitdepth = info['streams'][0]['bits_per_sample']
    # 16 bit-depth minimum since phase_limiter doesn't like 8
    bitdepth = 16 if bitdepth == 8 else bitdepth

    # Build the command line to run
    cmdline = []
    cmdline.append(PHASELIMITER_BIN)
    cmdline.extend([ "-reference", "-9",
                     "-reference_mode", "loudness",
                     "-ceiling_mode", "lowpass_true_peak",
                     "-ceiling", "-0.5",
                     "-mastering_mode", "mastering5",
                     "-mastering5_mastering_level", "0.7",
                     "-bit_depth", str(bitdepth),
                     "-input", filename,
                     "-output", outfile
                   ])

    # Connect stdin to prevent hang when in background
    stdout = ""
    stderr = ""
    process = subprocess.Popen(cmdline,
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               universal_newlines=True)
    process.stdin.write("\n\n\n\n\n")

    percent = 0
    helpers.setprogress(file_id, Tasks.MAST, 0)
    while True:
        line = process.stdout.readline()
        stdout += line
        p = re.compile('progression: ([\d.]+)')
        m = p.match(line)
        if m is not None:
            percent = float(m.group(1)) * 100
            helpers.setprogress(file_id, Tasks.MAST, percent)
        if process.poll() is not None:
            for line in process.stdout.readlines():
                stdout += line
            for line in process.stderr.readlines():
                stderr += line
            helpers.setprogress(file_id, Tasks.MAST, 100)
            break

    # Store the resulting file
    stored_location = filestore.store_file(file_id, outfile, f"{Tasks.MAST.value}.wav", private)

    # Make an MP3 website version
    mp3file = f"{scratch}/{Tasks.MAST.value}.mp3"
    helpers.make_website_mp3(outfile, mp3file)
    # Store the resulting file
    mp3_location = filestore.store_file(file_id, mp3file, f"{Tasks.MAST.value}.mp3", private)

    # Build the dict to return to caller
    ret = { "command": { "stdout": stdout, "stderr": stderr } }
    ret['output'] = stored_location
    ret['mp3'] = mp3_location
    filestore.copy_keys(file_id, public_keys, private, public)
    helpers.destroy_scratch_dir(scratch)
    return True, ret
