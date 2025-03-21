import sys
raise Exception()
sys.exit()

import os
import boto3
import re
import mimetypes

from boto3.s3.transfer import TransferConfig
s3 = boto3.resource('s3')
config = TransferConfig(multipart_threshold=64 * 1024 * 1024)

scratchfile = '/tmp/scratchfile'

srcname = 'licenselounge-public'
dstname = 'licenselounge-beats'
src = s3.Bucket(srcname)
dst = s3.Bucket(dstname)


def key_exists(key, section):
    results = s3.meta.client.list_objects_v2(Bucket=section, Prefix=key)
    return 'Contents' in results

### STILL IN LAB
#files = [ "stems.json", "stems-bass.wav", "stems-drums.wav", "stems-vocals.wav", "stems-guitar.wav", "stems-piano.wav", "stems-other.wav" ]
### TO PUBLIC
#files = [ "watermark.mp3", "original.json", "key-bpm.json", "coverart.*" ]
#files = [ "stems.json" ]
#### TO BEATS
#files = [ "mastering.wav", "original.*", "status.json" ]
#files = [ "stems-.*", "stems.json" ]
### NOWHERE YET
#files = [ "instrumental.wav", "lyrics.json", "lyrics.srt", "lyrics.tsv", "lyrics.txt", "lyrics.vtt" ]
#files = [ ".*.mp3" ]

pats = {}

for f in files:
    pats[f] = re.compile(f'jake/blues/{f}')

for o in src.objects.all():
    for f in files:
        m = pats[f].match(o.key)
        if m is not None:
            print(f'*Found: {o.key}')
            #s3.Object(srcname, o.key).delete()
            filename = scratchfile + "/" + o.key
            os.makedirs(os.path.split(scratchfile + "/" + o.key)[0], exist_ok=True)
            s3.Object(srcname, o.key).download_file(filename, Config=config)
            #if key_exists(o.key, dstname):
            #    print("**Key exists in dst, skipping...")
            #    continue
            #else:
            #    file_mime_type, _ = mimetypes.guess_type(o.key)
            #    extra = {'ContentType': file_mime_type} if file_mime_type is not None else None
            #    s3.Object(srcname, o.key).download_file(scratchfile, Config=config)
            #    print(f'>Downloaded: {src.name}/{o.key} to {scratchfile}')
            #    dst.upload_file(Filename=scratchfile, Key=o.key, Config=config, ExtraArgs=extra)
            #    print(f'<Uploaded: {scratchfile} to {dst.name}/{o.key}')


sys.exit()


##############

from tasks import filestore
import boto3
import mimetypes
from urllib.request import urlopen
import json

from boto3.s3.transfer import TransferConfig
s3 = boto3.resource('s3')
config = TransferConfig(multipart_threshold=64 * 1024 * 1024)

scratchfile = '/tmp/scratchfile'

srcname = 'licenselounge-public'
dstname = 'licenselounge-beats'
#src = s3.Bucket(srcname)
#dst = s3.Bucket(dstname)

with open('../rerun/beats.json') as f:
    b = json.load(f)

with open('../rerun/soundkits.json') as f:
    s = json.load(f)

bids = [y['id'] for y in b]
sids = [y['id'] for y in s]

blist = [ 'bars-desktop.png',
          'bars-mobile.png',
          'genre.json',
          'gfx.json',
          'instrumental.png',
          'key-bpm.json',
          'mastering.png',
          'original.json',
          'original.png',
          'stems-bass.png',
          'stems-drums.png',
          'stems-guitar.png',
          'stems-other.png',
          'stems-piano.png',
          'stems-vocals.png',
          'stems.json',
          'vocals.json',
          'watermark.mp3' ]

slist = [ 'inventory.json',
          'watermark.png' ]

for file_id in bids:
    for file in blist:
        if filestore.key_exists(file_id, file, srcname):
            filestore.copy_keys(file_id, [file], srcname, dstname)

for file_id in sids:
    for file in slist:
        if filestore.key_exists(file_id, file, srcname):
            filestore.copy_keys(file_id, [file], srcname, dstname)

sys.exit()

found = [ (y['id'], y['moods'][0]['name']) for y in b if y['moods'] != [] ]

for file_id, mood in found:
    print(f'*Found: {file_id} {mood}')
    file_mime_type, _ = mimetypes.guess_type("original.mp3")
    extra = {'ContentType': file_mime_type} if file_mime_type is not None else None
    s3.Object(srcname, f"{file_id}/original.mp3").download_file(scratchfile, Config=config)
    print(f'>Downloaded: {src.name}/{file_id}/original.mp3 to {scratchfile}')
    dst.upload_file(Filename=scratchfile, Key=f"moods/{mood}/{file_id}.mp3", Config=config, ExtraArgs=extra)
    print(f'<Uploaded: {scratchfile} to {dst.name}/moods/{mood}/{file_id}.mp3')



