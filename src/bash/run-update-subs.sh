#!/bin/bash
cd /home/ubuntu/raisin/repo/src
source raisin/bin/activate
python manage.py update-subs > /dev/null 2>&1
deactivate
