from taskdef import *
from . import helpers
from . import keybpm
from . import stemmer
from . import mastering
from . import instrumental
from . import lyrics
from . import midi
from . import coverart
from . import original
from . import watermark
from . import status
from . import soundkit
from . import inventory
from . import bars
from . import graphics

__all__ = ["execute"]

execute = {}
execute[Tasks.KBPM] = keybpm.execute
execute[Tasks.STEM] = stemmer.execute
execute[Tasks.MAST] = mastering.execute
execute[Tasks.INST] = instrumental.execute
execute[Tasks.LYRC] = lyrics.execute
execute[Tasks.MIDI] = midi.execute
execute[Tasks.COVR] = coverart.execute
execute[Tasks.ORIG] = original.execute
execute[Tasks.WTRM] = watermark.execute
execute[Tasks.STAT] = status.execute
execute[Tasks.OGSK] = soundkit.execute
execute[Tasks.ZINV] = inventory.execute
execute[Tasks.BARS] = bars.execute
execute[Tasks.WGFX] = graphics.execute
