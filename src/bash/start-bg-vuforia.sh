#!/bin/bash
cd /home/ubuntu/raisin/repo/src
source raisin/bin/activate
python manage.py bg-vuforia
deactivate
