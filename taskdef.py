from enum import Enum

class Tasks(Enum):
    ORIG = 'original' # Initialize the file store with the original
    WTRM = 'watermark' # Generate a watermarked version of the original
    KBPM = 'key-bpm' # Calculate key and BPM of original
    STEM = 'stems' # Identify and isolate stems from original
    MAST = 'mastering' # Master the original track
    INST = 'instrumental' # Produce and intrumental version from stems
    LYRC = 'lyrics' # Get the lyrics from the vocals stem
    MIDI = 'midi' # Produce a MIDI file (per stem?)
    COVR = 'coverart' # Generate cover art automatically
    STAT = 'status' # Save the status as JSON at the end
    BARS = 'bars' # Generate bar/waveform graphics for an original
    OGSK = 'soundkit' # Initialize filestore with soundkit
    ZINV = 'inventory' # Gather metadata about the contents of a zip

class State(Enum):
    INIT = "initial"
    PROG = "in-progress"
    WAIT = "waiting"
    COMP = "completed"
    FAIL = "failed"
    NA = "not-available"
