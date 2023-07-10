import os
import json
import subprocess
from taskdef import *
from . import helpers
from . import filestore
from config import CONFIG as conf

FFMPEG_BIN = conf['FFMPEG_BIN']
FILESTORE_BACKEND = conf['FILESTORE_BACKEND']

def execute(file_id, force=False):
    private, public = helpers.get_bucketnames(file_id)
    scratch = helpers.create_scratch_dir()
    # Short-circuit if the filestore already has assets we would produce
    public_keys = [ f"{Tasks.ORIG.value}.json" ]
    output_keys = [ f"{Tasks.ORIG.value}.wav",
                    f"{Tasks.ORIG.value}.mp3" ] + public_keys
    if not force and filestore.check_keys(file_id, output_keys, private):
        if not filestore.check_keys(file_id, public_keys, public):
            filestore.copy_keys(file_id, public_keys, private, public)
        helpers.destroy_scratch_dir(scratch)
        return

    # Get the external file and grab it's metadata
    try:
        if FILESTORE_BACKEND == "local":
            local_file = os.getenv('TESTFILE')
        else:
            local_file = filestore.retrieve_file(file_id, f"{Tasks.ORIG.value}", scratch, private)
    except:
        helpers.destroy_scratch_dir(scratch)
        return { 'message': f'File not found', 'failed': True }
    metadata = helpers.get_media_info(local_file)
    if not metadata:
        helpers.destroy_scratch_dir(scratch)
        return { 'message': f'File format not recognized', 'failed': True }
    fmt = metadata['format'].get('format_name')
    if fmt != 'wav' and fmt != 'aiff':
        helpers.destroy_scratch_dir(scratch)
        return { 'message': f'Not accepting this file format: {fmt}', 'failed': True }

    # Save the file info along side it
    ret = {}
    tempfile = f"{scratch}/{Tasks.ORIG.value}.json"
    with open(tempfile, 'w') as f:
        f.write(json.dumps(metadata, indent=2))
    ret['info'] = filestore.store_file(file_id, tempfile, f"{Tasks.ORIG.value}.json", private)

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
    outfile = f"{scratch}/{Tasks.ORIG.value}.wav"
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
    ret['output'] = filestore.store_file(file_id, outfile, f"{Tasks.ORIG.value}.wav", private)

    # Make an MP3 website version
    mp3file = f"{scratch}/{Tasks.ORIG.value}.mp3"
    helpers.make_website_mp3(outfile, mp3file)
    # Store the resulting file
    ret['mp3'] = filestore.store_file(file_id, mp3file, f"{Tasks.ORIG.value}.mp3", private)

    # Build the dict to return to caller
    ret["command"] = { "stdout": stdout, "stderr": stderr }
    filestore.copy_keys(file_id, public_keys, private, public)
    helpers.destroy_scratch_dir(scratch)
    return ret
