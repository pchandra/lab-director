#!/bin/bash

TMUX=`which tmux`

if [ X"$1" == X ]; then \
     echo -n "**Need exactly one arg for session name"
     $TMUX ls >/dev/null 2>&1
     if [ X$? == X0 ]; then \
          echo ", try one of these:"
          echo
          $TMUX ls
     else
          echo
     fi
     echo
     echo "--Create a new one with: $0 <session-name>"
     echo
     exit
fi

$TMUX ls 2>&1 | grep -e "^$1:" >/dev/null 2>&1
if [ X$? == X0 ]; then \
    $TMUX attach -t "$1"
else
    $TMUX new-session -s "$1"
fi
