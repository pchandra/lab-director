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

    # Interrogate file and grab some stats about it
    metadata = {}
    info = sf.info(local_file, verbose=True)
    metadata['channels'] = info.channels
    metadata['duration'] = info.duration
    metadata['format'] = info.format
    metadata['format_info'] = info.format_info
    metadata['frames'] = info.frames
    metadata['samplerate'] = info.samplerate
    metadata['subtype'] = info.subtype
    metadata['subtype_info'] = info.subtype_info
    metadata['verbose'] = info.extra_info
    # Save this to JSON
    tempfile = f"{scratch}/{Tasks.ORIG.value}.json"
    with open(tempfile, 'w') as f:
        f.write(json.dumps(metadata, indent=2))
    ret['info'] = filestore.store_file(file_id, tempfile, f"{Tasks.ORIG.value}.json")

    # XXX: This is a hack... assume it's a wave for tag removal
    wavname = local_file + '.wav'
    shutil.move(local_file, wavname)

    # Now strip any tags it might have in it
    with taglib.File(wavname, save_on_exit=True) as beat:
        beat.removeUnsupportedProperties(beat.unsupported)
    with taglib.File(wavname, save_on_exit=True) as beat:
        tags = []
        for tag in beat.tags.keys():
            tags.append(str(tag))
        for tag in tags:
            del beat.tags[tag]

    # Now run this through ffmpeg to translate as WAV
    outfile = f"{scratch}/{Tasks.ORIG.value}.wav"
    cmdline = []
    cmdline.append(FFMPEG_BIN)
    cmdline.extend([ "-i", wavname,
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
