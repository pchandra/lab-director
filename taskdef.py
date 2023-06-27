from enum import Enum

class Tasks(Enum):
    ORIG = 'original' # Initialize the file store with the original
    WTRM = 'watermark' # Generate a watermarked version of the original
    KBPM = 'key-bpm' # Calculate key and BPM of original
    STEM = 'stems' # Identify and isolate stems from original
    MAST = 'mastering' # Master the original track
    INST = 'instrumental' # Produce and intrumental version from stems
    VOCL = 'vocal' # Analyze vocal stem
    LYRC = 'lyrics' # Get the lyrics from the vocals stem
    MIDI = 'midi' # Produce a MIDI file (per stem?)
    STAT = 'status' # Save the status as JSON at the end
    BARS = 'bars' # Generate bar/waveform graphics for an original
    WGFX = 'gfx' # Generate detailed waveform graphics
    OGSK = 'soundkit' # Initialize filestore with soundkit
    ZINV = 'inventory' # Gather metadata about the contents of a zip
    KGFX = 'soundkit-gfx' # Create graphics for a soundkit preview file
    GENR = 'genre' # Run models to detect music genre
    CONV = 'convert' # Run a conversion task

class State(Enum):
    INIT = "initial"
    PROG = "in-progress"
    WAIT = "waiting"
    COMP = "completed"
    FAIL = "failed"
    NA = "not-available"
