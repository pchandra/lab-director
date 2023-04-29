from taskdef import *

# Some commononly tweaked, system-dependent variables
CONFIG = {}


###### General config for the whole suite

# The tasks that must be run for each Beat/Song
CONFIG['TASKS_BEAT'] = [ Tasks.ORIG,
                         Tasks.BARS,
                         Tasks.WTRM,
                         Tasks.KBPM,
                         Tasks.STEM,
                         Tasks.MAST,
                         Tasks.INST,
                         Tasks.LYRC,
                         Tasks.MIDI,
                         Tasks.COVR,
                         Tasks.STAT
                       ]

# The tasks that must be run for each Soundkit
CONFIG['TASKS_SOUNDKIT'] = [ Tasks.OGSK,
                             Tasks.COVR,
                             Tasks.ZINV,
                             Tasks.STAT
                           ]

###### Config section for Router

# Address for clients to use to talk to the Router
CONFIG['ROUTER_ADDR'] = '127.0.0.1'

# Address and port for the Router's frontend ZMQ sockets (Director is the client)
CONFIG['ROUTER_FRONTEND_BIND'] = '0.0.0.0'
CONFIG['ROUTER_FRONTEND_PORT'] = 1234

# Address and port for the Router's backend ZMQ sockets (Workers are the clients)
CONFIG['ROUTER_BACKEND_BIND'] = '0.0.0.0'
CONFIG['ROUTER_BACKEND_PORT'] = 3456

# Python 'Shelve' file used for the router to save state
CONFIG['ROUTER_SHELVE'] = 'saved-queue'


###### Config section for DIRECTOR

# Address for clients to use to talk to the Director
CONFIG['DIRECTOR_ADDR'] = '127.0.0.1'

# Address and port for the Director HTTP API to bind to (Workers and external tools are the clients)
CONFIG['DIRECTOR_BIND'] = '0.0.0.0'
CONFIG['DIRECTOR_PORT'] = 5678

# Python 'Shelve' file used for the director to save state
CONFIG['DIRECTOR_SHELVE'] = 'saved-status'


###### Config section for Workers

# Only run tasks from the following list on this worker node
CONFIG['ACCEPTABLE_WORK'] = [ x.value for x in Tasks ]
#CONFIG['ACCEPTABLE_WORK']  = [ Tasks.ORIG.value, Tasks.WTRM.value,
#                               Tasks.MAST.value, Tasks.KBPM.value,
#                               Tasks.STEM.value, Tasks.INST.value,
#                               Tasks.LYRC.value, Tasks.MIDI.value,
#                               Tasks.COVR.value, Tasks.STAT.value
#                             ]

# Directory Workers should use for scratch space when running tasks
CONFIG['WORK_DIR'] = '/tmp/SCRATCH'

# Should be either 'local' or 's3'
CONFIG['FILESTORE_BACKEND']='local'

# Directory to use for local filestore, if enabled
CONFIG['FILESTORE_DIR'] = '/tmp/STORE'

# Section name for public files, local: subdirectory, s3: bucket name
CONFIG['FILESTORE_PUBLIC'] = 'licenselounge-public'

# Section name for beat files, local: subdirectory, s3: bucket name
CONFIG['FILESTORE_BEATS'] = 'licenselounge-beats'

# Section name for soundkit files, local: subdirectory, s3: bucket name
CONFIG['FILESTORE_SOUNDKITS'] = 'licenselounge-soundkits'

# Multipart threshold setting for S3 uploads and downloads
CONFIG['MULTIPART_THRESHOLD'] = 64 * 1024 * 1024

# Wav file to use for watermarking process
CONFIG['WATERMARK_WAV'] = '/Users/chandra/ll/co/wav-mixer/stamps/ll-stamp.wav'

# Relative strength to apply to the watermark mixing (mark-maker tool)
CONFIG['WATERMARK_STRENGTH'] = "4"

# Relative strength to apply to the watermark mixing (mark-maker tool)
CONFIG['WATERMARK_DELAY'] = "2"

# Relative strength to apply to the watermark mixing (mark-maker tool)
CONFIG['WATERMARK_GAP'] = "0"

# Sound level for considering audio input to be silent
CONFIG['SILENCE_THRESHOLD'] = '-32dB'

# Max percent of silence allowed in a track, otherwise considered empty
CONFIG['SILENCE_PERCENT'] = 0.90

# Binary to run 'ffmpeg' tool
CONFIG['FFMPEG_BIN'] = '/usr/local/bin/ffmpeg'

# Binary to run 'ffprobe' tool
CONFIG['FFPROBE_BIN'] = '/usr/local/bin/ffprobe'

# Command to run 'keymaster' tool
CONFIG['KEYMASTER_BIN'] = '/Users/chandra/ll/co/key-bpm-finder/keymaster.py'

# Command to run the 'demucs' tool
CONFIG['DEMUCS_BIN'] = '/usr/local/bin/demucs'

# Command to run the 'phase_limiter' tool
CONFIG['PHASELIMITER_BIN'] = '/Users/chandra/ll/co/phaselimiter/bin/Release/phase_limiter'

# Command to run for 'wav-mixer' tool
CONFIG['WAVMIXER_BIN'] = '/Users/chandra/ll/co/wav-mixer/wav-mixer.py'

# Command to run for 'mark-maker' tool
CONFIG['MARKMAKER_BIN'] = '/Users/chandra/ll/co/wav-mixer/mark-maker.py'

# Command to run for 'bar-tender' tool
CONFIG['BARTENDER_BIN'] = '/Users/chandra/ll/co/wav-mixer/bar-tender.py'

# Command to run for 'zip-liner' tool
CONFIG['ZIPLINER_BIN'] = '/Users/chandra/ll/co/wav-mixer/zip-liner.py'

# Command to run for 'whisper' tool
CONFIG['WHISPER_BIN'] = '/usr/local/bin/whisper'

# Model for vocals to text, common choices are 'tiny', 'small', 'medium', 'large'
CONFIG['WHISPER_MODEL'] = "tiny"

# Location for JSON files for initial batch import
CONFIG['BATCH_BEAT_FILE'] = '/Users/chandra/ll/website/beats.json'
CONFIG['BATCH_SOUNDKIT_FILE'] ='/Users/chandra/ll/website/soundkits.json'

# Device to use for ML tools, either "cpu" or "cuda"
CONFIG['ML_DEVICE'] = "cpu"
