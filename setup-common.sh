#!/bin/bash

#############################
#
#  Common setup of utilities for all audiolab
#  node types on Ubuntu 22.04 base install.
#  The more specific 'setup' scripts call
#  this one also.
#
#############################

sudo apt-get install -y python3 python3-pip

python3 -m pip install -U zmq

BINDIR=~/.local/bin

mkdir -p $BINDIR
cp static/tmux-wrapper.sh $BINDIR/audiolab
chmod +x $BINDIR/audiolab
