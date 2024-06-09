#!/bin/bash
NAME="raisin_application"                                       # Name of the application

DJANGODIR=/home/ubuntu/raisin/repo/src/                   # Django project directory
VIRTUAL_ENV_PATH=/home/ubuntu/.virtualenvs/raisin

SOCKFILE=/home/ubuntu/raisin/gsock/gunicorn.sock    # we will communicte using this unix socket
LOG_FILE=/home/ubuntu/raisin/logs/gunicorn.log

USER=ubuntu                                               # the user to run as
GROUP=ubuntu                                              # the group to run as

NUM_WORKERS=9                                               # how many worker processes should Gunicorn spawn
DJANGO_SETTINGS_MODULE=raisin.settings                      # which settings file should Django use
DJANGO_WSGI_MODULE=raisin.wsgi                              # WSGI module name

echo "Starting $NAME" # Activate the virtual environment

cd $DJANGODIR

echo "Activating environment with PATH: $VIRTUAL_ENV_PATH - calling $VIRTUAL_ENV_PATH/bin/activate"
# source $VIRTUAL_ENV_PATH/bin/activate

# workon raisin

export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE
export PYTHONPATH=$DJANGODIR:$PYTHONPATH                    # Create the run directory if it does nopt exist

RUNDIR=$(dirname $SOCKFILE)
test -d $RUNDIR || mkdir -p $RUNDIR                         # Start your Django Unicorn

echo "RUNDIR: $RUNDIR"

# Programs meant to be run under supervisor should not daemonize themselves (do not use --daemon)
echo "$VIRTUAL_ENV_PATH/bin/gunicorn ${DJANGO_WSGI_MODULE}:application --name $NAME --workers $NUM_WORKERS --user=$USER --group=$GROUP --bind unix:$SOCKFILE --log-level=debug --log-file=$LOG_FILE --timeout 100"
exec $VIRTUAL_ENV_PATH/bin/gunicorn ${DJANGO_WSGI_MODULE}:application --name $NAME --workers $NUM_WORKERS --user=$USER --group=$GROUP --bind unix:$SOCKFILE --log-level=debug --log-file=$LOG_FILE --timeout 100