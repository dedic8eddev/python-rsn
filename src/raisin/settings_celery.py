import os
import datetime

from raisin.settings import TIME_ZONE

CELERY_APP = 'my_celery.celery_app'
CELERYD_NODES = 'worker'
CELERYD_CHDIR = '/src/my_celery/'
LOGFILE_PATH_DIR = os.getenv("RAISIN_LOGFILE_PATH_DIR")
CELERYD_LOG_FILE = os.path.join(LOGFILE_PATH_DIR, "sql-log.log")
CELERYD_MULTI = 'multi'

CELERY_CREATE_DIRS = True

CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

# using .env (.env_dev) for docker
CELERY_RESULT_BACKEND = os.getenv("RAISIN_CELERY_RESULT_BACKEND",
                                  'redis://127.0.0.1:6379/0')
CELERY_TIMEZONE = TIME_ZONE
CELERY_IGNORE_RESULT = False
CELERY_IMPORTS = [
    'my_celery.tasks'
]

CELERY_BIN = 'raisin/bin'

# using .env (.env_dev) for docker
CELERY_BROKER_URL = os.getenv("RAISIN_CELERY_BROKER_URL",
                              'redis://127.0.0.1:6379/0')

CELERY_BEAT_SCHEDULE_STR = os.getenv('RAISIN_CELERY_BEAT_SCHEDULE')
CELERY_BEAT_SCHEDULE = eval(CELERY_BEAT_SCHEDULE_STR)
