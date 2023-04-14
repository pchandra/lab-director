import os
import re
import subprocess
from taskdef import *
from . import helpers

PHASELIMITER_BIN = '/Users/chandra/ll/co/phaselimiter/bin/Release/phase_limiter'

def execute(filename, status):
    outfile = f"{helpers.WORK_DIR}/{os.path.basename(filename)}-{Tasks.MAST.value}.wav"
    # Build the command line to run
    cmdline = []
    cmdline.append(PHASELIMITER_BIN)
    cmdline.extend([ "-reference", "-9",
                     "-reference_mode", "loudness",
                     "-ceiling_mode", "lowpass_true_peak",
                     "-ceiling", "-0.5",
                     "-mastering_mode", "mastering5",
                     "mastering5_mastering_level", "0.7",
                     "-input", filename,
                     "-output", outfile
                   ])
    # Execute the command if we don't already have output
    stdout = ""
    stderr = ""
    if Tasks.MAST.value in status and State.COMP.value in status[Tasks.MAST.value] and "stdout" in status[Tasks.MAST.value][State.COMP.value]:
        stdout = status[Tasks.MAST.value][State.COMP.value]["stdout"]
        stderr = status[Tasks.MAST.value][State.COMP.value]["stderr"]
    if not os.path.exists(outfile):
        # Connect stdin to prevent hang when in background
        process = subprocess.Popen(cmdline,
                                   stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   universal_newlines=True)
        process.stdin.write("\n\n\n\n\n")

        percent = 0
        helpers.setprogress(status['id'], Tasks.MAST, 0)
        while True:
            line = process.stdout.readline()
            stdout += line
            p = re.compile('progression: ([\d.]+)')
            m = p.match(line)
            if m is not None:
                percent = float(m.group(1)) * 100
                helpers.setprogress(status['id'], Tasks.MAST, percent)
            if process.poll() is not None:
                for line in process.stdout.readlines():
                    stdout += line
                for line in process.stderr.readlines():
                    stderr += line
                helpers.setprogress(status['id'], Tasks.MAST, 100)
                break

    # Build the dict to return to caller
    ret = { "command": { "stdout": stdout, "stderr": stderr } }
    ret["output"] = outfile
    return ret
