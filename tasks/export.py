import os
import json
import subprocess
from taskdef import *
import taskapi as api
from . import helpers
from . import filestore
from config import CONFIG as conf

FFMPEG_BIN = conf['FFMPEG_BIN']
FILESTORE_SCRATCH = conf['FILESTORE_SCRATCH']
FILESTORE_PURCHASES = conf['FILESTORE_PURCHASES']

def _tag(msg):
    return f"{os.path.basename(__file__)}: {msg}"

def _make_archive(arch_file, fmt, arch_dir):
    if fmt == 'zip':
        import zipfile
        with zipfile.ZipFile(arch_file, 'w') as archive:
            for file in os.listdir(arch_dir):
                archive.write(f"{arch_dir}/{file}", arcname=file, compress_type = zipfile.ZIP_DEFLATED)
    elif fmt == 'tgz':
        import tarfile
        with tarfile.open(arch_file, "w:gz") as archive:
            for file in os.listdir(arch_dir):
                archive.add(f"{arch_dir}/{file}", file)

def _get_assets(file_id, directory, key, private, public):
    """This function grabs all the assets for a special type"""
    try:
        instrumental = None
        # Always need the original WAV
        filestore.retrieve_file(file_id, f"{Tasks.ORIG.value}.wav", directory, private)
        helpers.make_website_mp3(f"{directory}/{Tasks.ORIG.value}.wav", f"{directory}/{Tasks.ORIG.value}.mp3", high_quality=True)
        if key == 'purchase-mp3':
            os.remove(f"{directory}/{Tasks.ORIG.value}.wav")
        if key in [ 'all', 'purchase-stems' ]:
            # Get the stem metadata from the filestore
            stem_json = filestore.retrieve_file(file_id, f"{Tasks.STEM.value}.json", directory, public)
            metadata = None
            with open(stem_json, 'r') as f:
                metadata = json.load(f)
            os.remove(f"{directory}/{Tasks.STEM.value}.json")
            for stem in metadata['stems']:
                filestore.retrieve_file(file_id, stem, directory, private)
            instrumental = metadata['instrumental']
        if key == 'all':
            filestore.retrieve_file(file_id, f"{Tasks.MAST.value}.wav", directory, private)
            if not instrumental:
                filestore.retrieve_file(file_id, f"{Tasks.INST.value}.wav", directory, private)
        return True
    except:
        return False

def export(file_id, key, fmt):
    private, public = helpers.get_bucketnames(file_id)
    status = api.get_status(file_id)

    if status['type'] in [ 'beat', 'song' ]:
        # Lots of sanity and error checking first
        special = [ 'all', 'purchase-mp3', 'purchase-wav', 'purchase-stems' ]
        if key in special:
            formats = [ 'zip', 'tgz' ]
        else:
            formats = [ 'mp3', 'aiff', 'flac', 'ogg', 'wav' ]

        # Screen acceptable input we support
        if not fmt in formats:
            return False, _tag(f"format {fmt} isn't accepted for {key}")

        # Short-circuit on format conversion if the filestore already has it
        output_keys = [ f"{key}.{fmt}" ]
        if key not in special and filestore.check_keys(file_id, output_keys, FILESTORE_SCRATCH):
            return True, _tag(f"{key}.{fmt} already exists for {file_id}")

        # Ok, we're going to have to do some work
        scratch = helpers.create_scratch_dir()

        # Do special cases
        if key in special:
            arch_dir = f"{scratch}/{key}"
            os.makedirs(arch_dir, exist_ok=True)
            arch_file = f"{scratch}/{key}.{fmt}"
            if _get_assets(file_id, arch_dir, key, private, public):
                _make_archive(arch_file, fmt, arch_dir)
                bucket = FILESTORE_SCRATCH if key == 'all' else FILESTORE_PURCHASES
                filestore.store_file(file_id, arch_file, f"{key}.{fmt}", bucket)
                ret = True, _tag(f"{key}.{fmt} successfully created for {file_id}")
            else:
                ret = False, _tag(f"request {key} didn't find assets for {file_id}")
            helpers.destroy_scratch_dir(scratch)
            return ret

        try:
            infile = filestore.retrieve_file(file_id, f"{key}.wav", scratch, private)
        except:
            helpers.destroy_scratch_dir(scratch)
            return False, _tag(f"file {key}.wav isn't found for {file_id}")

        # Special case for WAV requests
        if fmt == 'wav':
            outfile = infile
        else:
            outfile = f"{scratch}/{key}.{fmt}"

            # #execute the command
            cmdline = []
            cmdline.append(FFMPEG_BIN)
            cmdline.extend([ "-i", infile,
                             "-v", "quiet",
                             "-y"
                           ])
            if key == 'mp3' or key == 'ogg':
                cmdline.append("-b:a", "320k")
            cmdline.append(outfile)
            process = subprocess.Popen(cmdline,
                                       stdin=subprocess.PIPE,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,
                                       universal_newlines=True)
            stdout, stderr = process.communicate(input="\n\n\n\n\n")

        filestore.store_file(file_id, outfile, f"{key}.{fmt}", FILESTORE_SCRATCH)
        helpers.destroy_scratch_dir(scratch)
        return True, _tag(f"{key}.{fmt} successfully created for {file_id}")
    elif status['type'] == 'soundkit':
        special = [ 'all', 'purchase' ]
        formats = [ 'zip' ]
        if not key in special:
            return False, _tag(f"key {key} isn't accepted for {file_id}")
        if not fmt in formats:
            return False, _tag(f"format {fmt} isn't accepted for {key}")
        scratch = helpers.create_scratch_dir()
        try:
            skfile = filestore.retrieve_file(file_id, f"{Tasks.OGSK.value}.zip", scratch, private)
        except:
            helpers.destroy_scratch_dir(scratch)
            return False, _tag(f"file {Tasks.OGSK.value}.zip isn't found for {file_id}")
        bucket = FILESTORE_SCRATCH if key == 'all' else FILESTORE_PURCHASES
        filestore.store_file(file_id, skfile, f"{key}.{fmt}", bucket)
        helpers.destroy_scratch_dir(scratch)
        return True, _tag(f"{key}.{fmt} successfully created for {file_id}")

    return False, _tag(f"request {fmt} isn't accepted for {key}")
