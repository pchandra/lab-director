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
cp static/tmux-wrapper.sh $BINDIR/audiolab_tmux.sh
chmod +x $BINDIR/audiolab_tmux.sh

OUTFILE=$BINDIR/audiolab
touch $OUTFILE
chmod +x $OUTFILE
echo "#!/bin/bash" > $OUTFILE
echo "AL_TYPE=\"$AL_TYPE\"" >> $OUTFILE
echo "AL_PROCESS1=\"$AL_PROCESS1\"" >> $OUTFILE
echo "AL_PROCESS2=\"$AL_PROCESS2\"" >> $OUTFILE
echo "exec $BINDIR/audiolab_tmux.sh" >> $OUTFILE
