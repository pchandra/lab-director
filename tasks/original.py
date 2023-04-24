import json
import shutil
import subprocess
import taglib
import soundfile as sf
from taskdef import *
from . import helpers
from . import filestore
from config import CONFIG as conf

FFMPEG_BIN = conf['FFMPEG_BIN']

def execute(file_id, force=False):
    # Short-circuit if the filestore already has assets we would produce
    output_keys = [ f"{Tasks.ORIG.value}", f"{Tasks.ORIG.value}.json", f"{Tasks.ORIG.value}.wav", f"{Tasks.ORIG.value}.mp3" ]
    if not force and filestore.check_keys(file_id, output_keys):
        return

    # Proceed with running this task
    ret = {}
    scratch = helpers.create_scratch_dir()
    # Get the external file and store it as-is
    local_file = filestore.get_external_file(file_id, scratch)
    ret['original'] = filestore.store_file(file_id, local_file, f"{Tasks.ORIG.value}")

    # Save the file info along side it
    metadata = helpers.get_audio_info(local_file)
    tempfile = f"{scratch}/{Tasks.ORIG.value}.json"
    with open(tempfile, 'w') as f:
        f.write(json.dumps(metadata, indent=2))
    ret['info'] = filestore.store_file(file_id, tempfile, f"{Tasks.ORIG.value}.json")

    # Screen to ensure we have an AIFF or WAV file
    fmt = metadata['format'].get('format_name')
    extension = '.aiff' if fmt == 'aiff' else '.wav' if fmt == 'wav' else None
    if extension is None:
        return { 'message': f'File format not recognized: {fmt}', 'failed': True }
    channels = metadata['streams'][0]['channels']
    srate = metadata['streams'][0]['sample_rate']
    ssize = metadata['streams'][0]['bits_per_sample']
    audioname = local_file + extension
    shutil.move(local_file, audioname)

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
    cmdline.extend([ "-i", audioname,
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
    ret['output'] = filestore.store_file(file_id, outfile, f"{Tasks.ORIG.value}.wav")

    # Run FFMPEG to make MP3 version
    mp3file = f"{scratch}/{Tasks.ORIG.value}.mp3"
    # Run an FFMPEG cmd to compress to mp3
    cmdline = []
    cmdline.append(FFMPEG_BIN)
    cmdline.extend([ "-i", outfile,
                     "-v", "quiet",
                     "-b:a", "320k",
                     "-y"
                   ])
    cmdline.append(mp3file)
    process = subprocess.Popen(cmdline,
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               universal_newlines=True)
    stdout, stderr = process.communicate(input="\n\n\n\n\n")

    # Store the resulting file
    ret['mp3'] = filestore.store_file(file_id, mp3file, f"{Tasks.ORIG.value}.mp3")

    # Build the dict to return to caller
    ret["command"] = { "stdout": stdout, "stderr": stderr }
    helpers.destroy_scratch_dir(scratch)
    return ret
