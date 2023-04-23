#!/bin/bash

#############################
#
#  DIRECTOR/ROUTER: on Ubuntu 22.04 base install, several 
#  other tools need to be installed in order to run a 
#  director/router node
#
#############################

sudo apt-get install -y python3 python3-pip

python3 -m pip install -U Flask Flask-shelve zmq
