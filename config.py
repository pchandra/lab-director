# Some commononly tweaked, system-dependent variables
CONFIG = {}


###### Config section for Router

# Address for clients to use to talk to the Router
CONFIG['ROUTER_ADDR'] = '127.0.0.1'

# Address and port for the Router's frontend ZMQ sockets (Director is the client)
CONFIG['ROUTER_FRONTEND_BIND'] = '0.0.0.0'
CONFIG['ROUTER_FRONTEND_PORT'] = 3456

# Address and port for the Router's backend ZMQ sockets (Workers are the clients)
CONFIG['ROUTER_BACKEND_BIND'] = '0.0.0.0'
CONFIG['ROUTER_BACKEND_PORT'] = 3457

# Python 'Shelve' file used for the router to save state
CONFIG['ROUTER_SHELVE'] = 'saved-queue'


###### Config section for DIRECTOR

# Address for clients to use to talk to the Director
CONFIG['DIRECTOR_ADDR'] = '127.0.0.1'

# Address and port for the Director HTTP API to bind to (Workers and external tools are the clients)
CONFIG['DIRECTOR_BIND'] = '0.0.0.0'
CONFIG['DIRECTOR_PORT'] = 5000

# Python 'Shelve' file used for the director to save state
CONFIG['DIRECTOR_SHELVE'] = 'saved-status'


###### Config section for Workers

# Directory Workers should use for scratch space when running tasks
CONFIG['WORK_DIR'] = '/tmp/SCRATCH'

# Should be either 'local' or 's3'
CONFIG['FILESTORE_BACKEND']='local'

# Directory to use for local filestore, if enabled
CONFIG['FILESTORE_DIR'] = '/tmp/STORE'

# Bucket name to use for s3 filestore, if enabled
CONFIG['FILESTORE_BUCKETNAME'] = 'licenselounge-audiolab'

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
CONFIG['SILENCE_PERCENT'] = 0.95

# Binary to run 'ffmpeg' tool
CONFIG['FFMPEG_BIN'] = '/usr/local/bin/ffmpeg'

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

# Command to run for 'whisper' tool
CONFIG['WHISPER_BIN'] = '/usr/local/bin/whisper'

# Model for vocals to text, common choices are 'tiny', 'small', 'medium', 'large'
CONFIG['WHISPER_MODEL'] = "tiny"

# Location for JSON files for initial batch import
CONFIG['BATCH_BEAT_FILE'] = '/Users/chandra/ll/website/beats.json'
CONFIG['BATCH_SOUNDKIT_FILE'] ='/Users/chandra/ll/website/soundkits.json'

# Device to use for ML tools, either "cpu" or "cuda"
CONFIG['ML_DEVICE'] = "cpu"
