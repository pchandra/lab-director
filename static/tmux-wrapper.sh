#!/bin/sh

TMUX=`which tmux`
HOST="$AL_TYPE"
$TMUX attach -t $HOST || sleep 1; $TMUX new-session -s $HOST \; \
     new-window -n "$AL_PROCESS1" \; \
     new-window -n "$AL_PROCESS2" \;
