#!/bin/bash

DIR=`dirname "$(realpath $0)"`

if [ X"$TBBROOT" == X ]; then \
    source /opt/intel/oneapi/setvars.sh --
fi
$DIR/phase_limiter.real $@
