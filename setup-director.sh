#!/bin/bash

#############################
#
#  DIRECTOR/ROUTER: on Ubuntu 22.04 base install, several 
#  other tools need to be installed in order to run a 
#  director/router node
#
#############################

./setup-common.sh

python3 -m pip install -U Flask Flask-shelve waitress Paste
