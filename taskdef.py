from enum import Enum

class Tasks(Enum):
    ORIG = 'original' # Initialize the file store with the original
    WTRM = 'watermark' # Generate a watermarked version of the original
    KBPM = 'key-bpm' # Calculate key and BPM of original
    STEM = 'stems' # Identify and isolate stems from original
    MAST = 'mastering' # Master the original track
    INST = 'instrumental' # Produce and intrumental version from stems
    VOCL = 'vocals' # Analyze vocal stem
    LYRC = 'lyrics' # Get the lyrics from the vocals stem
    MIDI = 'midi' # Produce a MIDI file (per stem?)
    STAT = 'status' # Save the status as JSON at the end
    BARS = 'bars' # Generate bar/waveform graphics for an original
    WGFX = 'gfx' # Generate detailed waveform graphics
    OGSK = 'soundkit' # Initialize filestore with soundkit
    ZINV = 'inventory' # Gather metadata about the contents of a zip
    KGFX = 'soundkit-gfx' # Create graphics for a soundkit preview file
    GENR = 'genre' # Run models to detect music genre
    EXPT = 'export' # Run an export task

class TaskState(Enum):
    INIT = "initial"
    PROG = "in-progress"
    WAIT = "waiting"
    COMP = "completed"
    FAIL = "failed"
    NA = "not-available"

# The tasks that are automatically run for each beat/song
TASKS_BEAT = [ Tasks.ORIG,
               Tasks.BARS,
               Tasks.KBPM,
               Tasks.GENR,
               Tasks.STEM,
               Tasks.MAST,
               Tasks.WTRM,
               Tasks.INST,
               Tasks.VOCL,
               Tasks.LYRC,
               Tasks.WGFX,
               Tasks.STAT ]

TASKS_SONG = TASKS_BEAT

# The tasks that are automatically run for each soundkit
TASKS_SOUNDKIT = [ Tasks.OGSK,
                   Tasks.ZINV,
                   Tasks.KGFX,
                   Tasks.STAT ]
