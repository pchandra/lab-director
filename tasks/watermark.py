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

def execute(tg, force=False):
    if tg.status['type'] not in [ 'beat', 'song' ]:
        return False, helpers.msg('Track is not a beat or song')
    # Short-circuit if the filestore already has assets we would produce
    tg.add_public([ f"{Tasks.WTRM.value}.mp3" ])
    if not force and tg.check_keys():
        return True, helpers.msg('Already done')

    filename = tg.get_file(f"{Tasks.MAST.value}.wav")
    if filename is None:
        return False, helpers.msg(f'Input file not found: {Tasks.MAST.value}.wav')
    outfile = f"{tg.scratch}/{Tasks.WTRM.value}.wav"
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

    # Make an MP3 website version
    mp3file = f"{tg.scratch}/{Tasks.WTRM.value}.mp3"
    helpers.make_website_mp3(outfile, mp3file)
    # Store the resulting file
    ret['output'] = tg.put_file(mp3file, f"{Tasks.WTRM.value}.mp3")
    ret["phase2"] = { "stdout": stdout, "stderr": stderr }
    return True, ret
