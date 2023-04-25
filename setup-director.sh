#!/bin/bash

#############################
#
#  DIRECTOR/ROUTER: on Ubuntu 22.04 base install, several 
#  other tools need to be installed in order to run a 
#  director/router node
#
#############################

export AL_TYPE="al-leader"
export AL_PROCESS1="director"
export AL_PROCESS2="router"

./setup-common.sh

python3 -m pip install -U Flask Flask-shelve
