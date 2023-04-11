import os
import time
import json
import subprocess
from taskdef import *
import taskapi as api

# Working directory for tools to operate
WORK_DIR = '/tmp'

_task_bin = {}
_task_bin[Tasks.KBPM] = '/Users/chandra/ll/co/key-bpm-finder/keymaster-json.py'
_task_bin[Tasks.STEM] = '/usr/local/bin/demucs'
_task_bin[Tasks.MAST] = '/Users/chandra/ll/co/phaselimiter/bin/Release/phase_limiter'
_task_bin[Tasks.INST] = '/Users/chandra/ll/co/wav-mixer/wav-mixer.py'
_task_bin[Tasks.LYRC] = '/usr/local/bin/whisper'
_task_bin[Tasks.MIDI] = '/usr/local/bin/basic-pitch'
_task_bin[Tasks.COVR] = '/bin/echo'

def _run_key_bpm_finder(filename, status):
    # Build the command line to run
    cmdline = []
    cmdline.append('/usr/local/bin/python3.9')
    cmdline.append(_task_bin[Tasks.KBPM])
    cmdline.append(filename)
    # Execute the command
    process = subprocess.Popen(cmdline, 
                               stdout=subprocess.PIPE,
                               universal_newlines=True)
    stdout, _ = process.communicate()
    # The tool outputs JSON so return it as a dict
    return json.loads(stdout)

def _get_model():
    # This is the model name we'll run, must be one of:
    #   htdemucs_6s htdemucs htdemucs_ft mdx mdx_extra hdemucs_mmi
    return "htdemucs_6s"

def _stems_for_model(model):
    stems = [ "bass", "drums", "other", "vocals"]
    if model == "htdemucs_6s":
        stems.append("guitar")
        stems.append("piano")
    return stems

def _run_demucs(filename, status):
    model = _get_model()
    stems = _stems_for_model(model)
    outbase = f"{WORK_DIR}/{model}/{os.path.basename(filename)}"
    # Build the command line to run
    cmdline = []
    cmdline.append(_task_bin[Tasks.STEM])
    cmdline.extend([ "-d", "cpu",
                     "-n", model,
                     "-o", WORK_DIR,
                     "--filename", "{track}-{stem}.{ext}"
                   ])
    cmdline.append(filename)
    # Execute the command if we don't already have output
    outbase = f"{WORK_DIR}/{model}/{os.path.basename(filename)}"
    stdout = None
    stderr = None
    if Tasks.STEM.value in status and State.COMP.value in status[Tasks.STEM.value] and "stdout" in status[Tasks.STEM.value][State.COMP.value]:
        stdout=status[Tasks.STEM.value][State.COMP.value]["stdout"]
        stderr=status[Tasks.STEM.value][State.COMP.value]["stderr"]
    if not os.path.exists(f"{outbase}-{stems[0]}.wav"):
        # Connect stdin to prevent hang when in background
        process = subprocess.Popen(cmdline,
                                   stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   universal_newlines=True)
        stdout, stderr = process.communicate(input="\n\n\n\n\n")
    # Build the dict to return to caller
    ret = { "model": model, "stdout": stdout, "stderr": stderr }
    ret[model] = {}
    for stem in stems:
        ret[model][stem] = f"{outbase}-{stem}.wav"
    return ret

def _run_phaselimiter(filename, status):
    outfile = f"{WORK_DIR}/{os.path.basename(filename)}-{Tasks.MAST.value}.wav"
    # Build the command line to run
    cmdline = []
    cmdline.append(_task_bin[Tasks.MAST])
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
    stdout = None
    stderr = None
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
        stdout, stderr = process.communicate(input="\n\n\n\n\n")
    # Build the dict to return to caller
    ret = { "stdout": stdout, "stderr": stderr }
    ret["output"] = outfile
    return ret

def _run_wav_mixer(filename, status):
    model = _get_model()
    stems = _stems_for_model(model)
    outfile = f"{WORK_DIR}/{os.path.basename(filename)}-{Tasks.INST.value}.wav"
    # Build the command line to run
    cmdline = []
    cmdline.append(_task_bin[Tasks.INST])
    cmdline.extend([ "-o", outfile ])
    # Add all the stems except the vocal track
    stems.remove("vocals")
    for stem in stems:
        cmdline.append(status[Tasks.STEM.value][State.COMP.value][model][stem])
    # Execute the command if we don't already have output
    stdout = None
    stderr = None
    if Tasks.INST.value in status and State.COMP.value in status[Tasks.INST.value] and "stdout" in status[Tasks.INST.value][State.COMP.value]:
        stdout = status[Tasks.INST.value][State.COMP.value]["stdout"]
        stderr = status[Tasks.INST.value][State.COMP.value]["stderr"]
    if not os.path.exists(outfile):
        # Connect stdin to prevent hang when in background
        process = subprocess.Popen(cmdline,
                                   stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   universal_newlines=True)
        stdout, stderr = process.communicate(input="\n\n\n\n\n")
    # Build the dict to return to caller
    ret = { "stdout": stdout, "stderr": stderr }
    ret["output"] = outfile
    return ret

def _run_whisper(filename, status):
    model = _get_model()
    outdir = f"{WORK_DIR}/{os.path.basename(filename)}-{Tasks.LYRC.value}"
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    # Build the command line to run
    cmdline = []
    cmdline.append(_task_bin[Tasks.LYRC])
    cmdline.extend([ "--language", "en",
                     "--model", "medium",
                     "--output_dir", outdir
                   ])
    # Only use the vocals stem for this input
    cmdline.append(status[Tasks.STEM.value][State.COMP.value][model]["vocals"])
    # Execute the command if we don't already have output
    stdout = None
    stderr = None
    if Tasks.LYRC.value in status and State.COMP.value in status[Tasks.LYRC.value] and "stdout" in status[Tasks.LYRC.value][State.COMP.value]:
        stdout = status[Tasks.INST.value][State.COMP.value]["stdout"]
        stderr = status[Tasks.INST.value][State.COMP.value]["stderr"]
    if not os.path.exists(outdir + "/vocals.srt"):
        # Connect stdin to prevent hang when in background
        process = subprocess.Popen(cmdline,
                                   stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   universal_newlines=True)
        stdout, stderr = process.communicate(input="\n\n\n\n\n")
    # Build the dict to return to caller
    ret = { "stdout": stdout, "stderr": stderr }
    ret["json"] = json.load(outdir + "/vocals.json")
    ret["srt"] = outdir + "/vocals.srt"
    with open(outdir + "/vocals.txt", "r") as f:
        ret["fulltext"] = f.readlines()
    return ret

def _run_basic_pitch(filename, status):
    time.sleep(30)
    return {}

def _run_dalle2(filename, status):
    time.sleep(30)
    return {}

execute = {}
execute[Tasks.KBPM] = _run_key_bpm_finder
execute[Tasks.STEM] = _run_demucs
execute[Tasks.MAST] = _run_phaselimiter
execute[Tasks.INST] = _run_wav_mixer
execute[Tasks.LYRC] = _run_whisper
execute[Tasks.MIDI] = _run_basic_pitch
execute[Tasks.COVR] = _run_dalle2
