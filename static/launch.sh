#!/bin/bash

## TEST-ONLY VARS
ROUTER_ADDR="172.31.25.52"
DIRECTOR_ADDR="172.31.25.52"
ACCEPTABLE_WORK="Tasks.STEM.value, Tasks.LYRC.value"
FILESTORE_PUBLIC="licenselounge-public-test"
FILESTORE_BEATS="licenselounge-beats-test"
FILESTORE_SOUNDKITS="licenselounge-soundkits-test"

# Switch to ubuntu user
sudo -u ubuntu /usr/bin/bash
cd /home/ubuntu

# Do config file generation from template
TEMPLATE="lab-director/config.py.template"
OUTPUT="lab-director/config.py"

# Variable substitutions
cp -f $TEMPLATE $OUTPUT
for i in ROUTER_ADDR \
         DIRECTOR_ADDR \
         ACCEPTABLE_WORK \
         FILESTORE_PUBLIC \
         FILESTORE_BEATS \
         FILESTORE_SOUNDKITS; do \
    echo "s/%%$i%%/${!i}/g"
    sed -i "s/%%$i%%/${!i}/g" $OUTPUT
done

# Launch workers in tmux
for n in work1 work2; do \
	tmux new-session -s "$n" "cd lab-director; python3 worker.py;bash -i" \; detach
