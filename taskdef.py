from enum import Enum

TASKS = [ "KEY-BPM",
          "STEMS",
          "MASTERING",
          "INSTRUMENTAL",
          "LYRICS",
          "MIDI",
          "COVERART"
        ]

class State(Enum):
    INIT = "INITIAL"
    PROG = "IN-PROGRESS"
    WAIT = "WAITING"
    COMP = "COMPLETED"
    FAIL = "FAILED"
    NA = "NOT-AVAILABLE"
