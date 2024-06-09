#!/bin/bash
cd /home/ubuntu/raisin/repo/src
. ./os-env-export-prod.sh
/home/ubuntu/.virtualenvs/raisin37/bin/python /home/ubuntu/raisin/repo/src/manage.py sendactivationreminders > /dev/null 2>&1
