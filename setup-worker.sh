#!/bin/bash

#############################
#
#  RUN: on Ubuntu 22.04 with a phase_limiter binary, 
#  there are a number of additional runtime dependencies
#
#############################

sudo apt-get install -y libsndfile1-dev

sudo apt-get install -y ffmpeg

wget -O- https://apt.repos.intel.com/intel-gpg-keys/GPG-PUB-KEY-INTEL-SW-PRODUCTS.PUB \
 | gpg --dearmor | sudo tee /usr/share/keyrings/oneapi-archive-keyring.gpg > /dev/null

echo "deb [signed-by=/usr/share/keyrings/oneapi-archive-keyring.gpg] https://apt.repos.intel.com/oneapi all main" \
 | sudo tee /etc/apt/sources.list.d/oneAPI.list

sudo apt-get update
sudo apt-get install -y intel-basekit

############
############ Must also copy the built 'phase_limiter' binary
############ to ~/bin/phase_limiter.real
############

mkdir -p ~/bin
cp static/phaselimiter-wrapper.sh ~/bin/phase_limiter
chmod +x ~/bin/phase_limiter

#############################
#
#  WORKER: on Ubuntu 22.04 several other tools need to be
#  installed in order to run a full worker node
#
#############################

export AL_TYPE="agent"
export AL_PROCESS1="worker1"
export AL_PROCESS2="worker2"

./setup-common.sh

# Third-party tools that we run
python3 -m pip install -U demucs openai-whisper basic-pitch

############
############ Get the home-made tools too using a
############ READ-ONLY github fine-grained token
############
############ pushd .
############ cd ~/
############ git config --global credential.helper store
############ git clone https://github.com/License-Lounge/lab-director
############ git clone https://github.com/License-Lounge/wav-mixer
############ git clone https://github.com/License-Lounge/key-bpm-finder
############ popd
############

# Dependencies for the home-made tools we just cloned
python3 -m pip install -U librosa matplotlib numpy numba pycairo boto3 pytaglib
