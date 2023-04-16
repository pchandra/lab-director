import subprocess
import soundfile
import librosa
from taskdef import *
from . import helpers
from . import filestore
from config import CONFIG as conf


FFMPEG_BIN = conf['FFMPEG_BIN']
MARKMAKER_BIN = conf['MARKMAKER_BIN']
WATERMARK_WAV = conf['WATERMARK_WAV']


def execute(file_id, status, force=False):
    # Short-circuit if the filestore already has assets we would produce
    output_keys = [ f"{Tasks.WTRM.value}.mp3" ]
    if not force and filestore.check_keys(file_id, status, output_keys):
        return

    # Proceed with running this task
    outfile = f"{helpers.WORK_DIR}/{status['uuid']}-{Tasks.WTRM.value}.wav"
    filename = filestore.retrieve_file(file_id, status, f"{Tasks.MAST.value}.wav", helpers.WORK_DIR + f"/{status['uuid']}")

    # Run the tool to make the watermarked version
    cmdline = []
    cmdline.append('/usr/local/bin/python3.9')
    cmdline.append(MARKMAKER_BIN)
    cmdline.extend([ "-o", outfile,
                     "-i", filename,
                     "-s", WATERMARK_WAV
                   ])
    # Connect stdin to prevent hang when in background
    stdout = None
    stderr = None
    process = subprocess.Popen(cmdline,
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               universal_newlines=True)
    stdout, stderr = process.communicate(input="\n\n\n\n\n")

    # Build the dict to return to caller
    ret = {}
    ret["phase1"] = { "stdout": stdout, "stderr": stderr }

    # Run FFMPEG to make MP3 version
    mp3file = f"{helpers.WORK_DIR}/{status['uuid']}-{Tasks.WTRM.value}.mp3"
    # Run an FFMPEG cmd to compress to mp3
    cmdline = []
    cmdline.append(FFMPEG_BIN)
    cmdline.extend([ "-i", outfile,
                     "-q:a", "2",
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
    ret['output'] = filestore.store_file(file_id, status, mp3file, f"{Tasks.WTRM.value}.mp3")
    ret["phase2"] = { "stdout": stdout, "stderr": stderr }
    return ret
