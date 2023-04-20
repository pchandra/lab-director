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
WATERMARK_STRENGTH = conf['WATERMARK_STRENGTH']
WATERMARK_DELAY =  conf['WATERMARK_DELAY']
WATERMARK_GAP = conf['WATERMARK_GAP']


def execute(file_id, force=False):
    # Short-circuit if the filestore already has assets we would produce
    output_keys = [ f"{Tasks.WTRM.value}.mp3" ]
    if not force and filestore.check_keys(file_id, output_keys):
        return

    # Proceed with running this task
    scratch = helpers.create_scratch_dir()
    outfile = f"{scratch}/{Tasks.WTRM.value}.wav"
    filename = filestore.retrieve_file(file_id, f"{Tasks.MAST.value}.wav", scratch)

    # Run the tool to make the watermarked version
    cmdline = []
    cmdline.append(MARKMAKER_BIN)
    cmdline.extend([ "-o", outfile,
                     "-i", filename,
                     "-s", WATERMARK_WAV,
                     "-m", WATERMARK_STRENGTH,
                     "-d", WATERMARK_DELAY,
                     "-g", WATERMARK_GAP
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
    mp3file = f"{scratch}/{Tasks.WTRM.value}.mp3"
    # Run an FFMPEG cmd to compress to mp3
    cmdline = []
    cmdline.append(FFMPEG_BIN)
    cmdline.extend([ "-i", outfile,
                     "-q:a", "3",
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
    ret['output'] = filestore.store_file(file_id, mp3file, f"{Tasks.WTRM.value}.mp3")
    ret["phase2"] = { "stdout": stdout, "stderr": stderr }
    helpers.destroy_scratch_dir(scratch)
    return ret
