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
    private, public = helpers.get_bucketnames(file_id)
    scratch = helpers.create_scratch_dir()
    # Short-circuit if the filestore already has assets we would produce
    public_keys = [ f"{Tasks.WTRM.value}.mp3" ]
    output_keys = [ ] + public_keys
    if not force and filestore.check_keys(file_id, output_keys, private):
        if not filestore.check_keys(file_id, public_keys, public):
            filestore.copy_keys(file_id, public_keys, private, public)
        helpers.destroy_scratch_dir(scratch)
        return True, helpers.msg('Already done')

    filename = filestore.retrieve_file(file_id, f"{Tasks.MAST.value}.wav", scratch, private)
    if filename is None:
        helpers.destroy_scratch_dir(scratch)
        return False, helpers.msg(f'Input file not found: {Tasks.MAST.value}.wav')
    outfile = f"{scratch}/{Tasks.WTRM.value}.wav"
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
    mp3file = f"{scratch}/{Tasks.WTRM.value}.mp3"
    helpers.make_website_mp3(outfile, mp3file)
    # Store the resulting file
    ret['output'] = filestore.store_file(file_id, mp3file, f"{Tasks.WTRM.value}.mp3", private)
    ret["phase2"] = { "stdout": stdout, "stderr": stderr }
    filestore.copy_keys(file_id, public_keys, private, public)
    helpers.destroy_scratch_dir(scratch)
    return True, ret
