import re
import json
import subprocess
from taskdef import *
from . import helpers
from config import CONFIG as conf

FFMPEG_BIN = conf['FFMPEG_BIN']
PHASELIMITER_BIN = conf['PHASELIMITER_BIN']

def execute(tg, force=False):
    if tg.status['type'] not in [ 'beat', 'song', 'batch-item' ]:
        return False, helpers.msg('Track is not a beat, song, or batch-item')
    # Short-circuit if the filestore already has assets we would produce
    tg.add_public([ f"{Tasks.MAST.value}.png" ])
    tg.add_private([ f"{Tasks.MAST.value}.wav",
                     f"{Tasks.MAST.value}.mp3" ])
    if not force and tg.check_keys():
        return True, helpers.msg('Already done')

    filename = tg.get_file(f"{Tasks.ORIG.value}.wav")
    if filename is None:
        return False, helpers.msg(f'Input file not found: {Tasks.ORIG.value}.wav')
    outfile = f"{tg.scratch}/{Tasks.MAST.value}.wav"

    # Get the info for the original file to get the bit depth
    infofile = tg.get_file(f"{Tasks.ORIG.value}.json")
    if infofile is None:
        return False, helpers.msg(f'Input file not found: {Tasks.ORIG.value}.json')
    with open(infofile, 'r') as f:
        info = json.load(f)
    bitdepth = info['streams'][0]['bits_per_sample']
    sample_rate = info['streams'][0]['sample_rate']
    # Set some minimum standards for mastering output
    bitdepth = 16 if bitdepth == 8 else bitdepth
    sample_rate = 44100 if int(sample_rate) < 44100 else int(sample_rate)

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
    helpers.setprogress(tg.file_id, Tasks.MAST, 0)
    while True:
        line = process.stdout.readline()
        stdout += line
        p = re.compile('progression: ([\d.]+)')
        m = p.match(line)
        if m is not None:
            percent = float(m.group(1)) * 100
            helpers.setprogress(tg.file_id, Tasks.MAST, percent)
        if process.poll() is not None:
            for line in process.stdout.readlines():
                stdout += line
            for line in process.stderr.readlines():
                stderr += line
            helpers.setprogress(tg.file_id, Tasks.MAST, 100)
            break

    # Fix sampling rate
    sampfile = f"{tg.scratch}/{Tasks.MAST.value}.samp.wav"
    helpers.make_sample_rate(outfile, sampfile, sample_rate, bitdepth)
    outfile = sampfile

    # Store the resulting file
    stored_location = tg.put_file(outfile, f"{Tasks.MAST.value}.wav")

    # Make an MP3 website version
    mp3file = f"{tg.scratch}/{Tasks.MAST.value}.mp3"
    helpers.make_website_mp3(outfile, mp3file)
    # Make a temp PNG for it
    helpers.make_wave_png(mp3file)
    # Store the resulting files
    mp3_location = tg.put_file(mp3file, f"{Tasks.MAST.value}.mp3")
    png_location = tg.put_file(mp3file + ".png", f"{Tasks.MAST.value}.png")

    # Build the dict to return to caller
    ret = { "command": { "stdout": stdout, "stderr": stderr } }
    ret['output'] = stored_location
    ret['mp3'] = mp3_location
    ret['png'] = png_location
    return True, ret
