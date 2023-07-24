import os
import json
import subprocess
from taskdef import *
from . import helpers
from config import CONFIG as conf

FFMPEG_BIN = conf['FFMPEG_BIN']
FILESTORE_BACKEND = conf['FILESTORE_BACKEND']

def execute(tg, force=False):
    # Short-circuit if the filestore already has assets we would produce
    tg.add_public([ f"{Tasks.ORIG.value}.json",
                    f"{Tasks.ORIG.value}.png" ])
    tg.add_private([ f"{Tasks.ORIG.value}.wav",
                     f"{Tasks.ORIG.value}.mp3" ])
    if not force and tg.check_keys():
        return True, helpers.msg('Already done')

    # Get the external file and grab it's metadata
    local_file = tg.get_file(f"{Tasks.ORIG.value}")
    if local_file is None:
        return False, helpers.msg(f'Input file not found: {Tasks.ORIG.value}')
    metadata = helpers.get_media_info(local_file)
    if not metadata:
        return False, helpers.msg('File format not recognized')
    fmt = metadata['format'].get('format_name')
    if fmt != 'wav' and fmt != 'aiff':
        return False, helpers.msg(f'Not accepting this file format: {fmt}')

    # Save the file info along side it
    ret = {}
    tempfile = f"{tg.scratch}/{Tasks.ORIG.value}.json"
    with open(tempfile, 'w') as f:
        f.write(json.dumps(metadata, indent=2))
    ret['info'] = tg.put_file(tempfile, f"{Tasks.ORIG.value}.json")

    # Screen to ensure we have an AIFF or WAV file
    channels = metadata['streams'][0]['channels']
    srate = metadata['streams'][0]['sample_rate']
    ssize = metadata['streams'][0]['bits_per_sample']

    # Pick a lossless wav codec based on the input file
    codec = 'pcm_s16le'
    if ssize == 8:
        codec = 'pcm_u8'
    elif ssize == 16:
        codec = 'pcm_s16le'
    elif ssize == 24:
        codec = 'pcm_s24le'
    elif ssize == 32:
        codec = 'pcm_s32le'

    # Now run this through ffmpeg to translate as clean WAV file
    outfile = f"{tg.scratch}/{Tasks.ORIG.value}.wav"
    cmdline = []
    cmdline.append(FFMPEG_BIN)
    cmdline.extend([ "-i", local_file,
                     "-v", "quiet",
                     "-ac", str(channels),
                     "-ar", str(srate),
                     "-acodec", codec,
                     "-map_metadata", "-1",
                     "-y"
                   ])
    cmdline.append(outfile)
    process = subprocess.Popen(cmdline,
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               universal_newlines=True)
    stdout, stderr = process.communicate(input="\n\n\n\n\n")

    # Save it as the wav version of original to the filestore
    ret['output'] = tg.put_file(outfile, f"{Tasks.ORIG.value}.wav")

    # Make an MP3 website version
    mp3file = f"{tg.scratch}/{Tasks.ORIG.value}.mp3"
    helpers.make_website_mp3(outfile, mp3file)
    # Make a temp PNG for it
    helpers.make_wave_png(mp3file)
    # Store the resulting files
    ret['mp3'] = tg.put_file(mp3file, f"{Tasks.ORIG.value}.mp3")
    ret['png'] = tg.put_file(mp3file + ".png", f"{Tasks.ORIG.value}.png")

    # Build the dict to return to caller
    ret["command"] = { "stdout": stdout, "stderr": stderr }
    return True, ret
