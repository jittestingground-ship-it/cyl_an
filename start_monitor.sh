#!/bin/bash
# Activate venv and start system monitor Qt in the background
source /home/kw/cyl_a/venv/bin/activate
nohup python /home/kw/cyl_a/system_monitor_qt.py &
