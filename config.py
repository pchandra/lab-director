# Some commononly tweaked, system-dependent variables
CONFIG = {}

# Binary to run 'ffmpeg' tool
CONFIG['FFMPEG_BIN'] = '/usr/local/bin/ffmpeg'

# Command to run 'keymaster' tool
CONFIG['KEYBPM_BIN'] = '/Users/chandra/ll/co/key-bpm-finder/keymaster.py'

# Command to run the 'demucs' tool
CONFIG['DEMUCS_BIN'] = '/usr/local/bin/demucs'

# Command to run the 'phase_limiter' tool
CONFIG['PHASELIMITER_BIN'] = '/Users/chandra/ll/co/phaselimiter/bin/Release/phase_limiter'

# Command to run for 'wav-mixer' tool
CONFIG['WAVMIXER_BIN'] = '/Users/chandra/ll/co/wav-mixer/wav-mixer.py'

# Command to run for 'whisper' tool
CONFIG['WHISPER_BIN'] = '/usr/local/bin/whisper'

# Model for vocals to text, common choices are 'tiny', 'small', 'medium', 'large'
CONFIG['WHISPER_MODEL'] = "tiny"


# Directory workers should use for scratch space when running tasks
CONFIG['WORK_DIR'] = '/tmp/SCRATCH'

# Should be either 'local' or 's3'
CONFIG['FILESTORE_BACKEND']='local'

# Directory to use for local filestore, if enabled
CONFIG['FILESTORE_DIR'] = '/tmp/STORE'


# Python 'Shelve' file used for the director to save state
CONFIG['DIRECTOR_SHELVE'] = 'saved-status'

# Python 'Shelve' file used for the router to save state
CONFIG['ROUTER_SHELVE'] = 'saved-queue'
