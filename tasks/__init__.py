from taskdef import *
from . import keybpm
from . import stemmer
from . import mastering
from . import instrumental
from . import vocals
from . import lyrics
from . import midi
from . import original
from . import watermark
from . import status
from . import soundkit
from . import inventory
from . import kitgfx
from . import bars
from . import graphics
from . import genre
from . import export
from . import coverart
from . import radio
from . import upsize
from . import artwork

__all__ = ["execute", "ondemand"]

execute = {}
execute[Tasks.KBPM] = keybpm.execute
execute[Tasks.STEM] = stemmer.execute
execute[Tasks.MAST] = mastering.execute
execute[Tasks.INST] = instrumental.execute
execute[Tasks.VOCL] = vocals.execute
execute[Tasks.MIDI] = midi.execute
execute[Tasks.ORIG] = original.execute
execute[Tasks.WTRM] = watermark.execute
execute[Tasks.STAT] = status.execute
execute[Tasks.OGSK] = soundkit.execute
execute[Tasks.ZINV] = inventory.execute
execute[Tasks.BARS] = bars.execute
execute[Tasks.WGFX] = graphics.execute
execute[Tasks.GENR] = genre.execute

ondemand = {}
ondemand[Tasks.EXPT.value] = export.ondemand
ondemand[Tasks.COVR.value] = coverart.ondemand
ondemand[Tasks.OGAW.value] = artwork.ondemand
ondemand[Tasks.KGFX.value] = kitgfx.ondemand
ondemand[Tasks.RDIO.value] = radio.ondemand
ondemand[Tasks.LYRC.value] = lyrics.ondemand
ondemand[Tasks.UPSZ.value] = upsize.ondemand
