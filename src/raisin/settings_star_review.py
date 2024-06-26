"""
Django settings for raisin project.

Generated by 'django-admin startproject' using Django 1.10.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.10/ref/settings/
"""

import os

from .settings_common import MEDIA_ROOT

RELEVANCY_KEYWORDS_FILEPATH = os.path.join(MEDIA_ROOT, 'data', 'relevancy_keywords.txt')  # noqa
RELEVANCY_KEYWORDS_FILEPATH_TMP = os.path.join(MEDIA_ROOT, 'data', 'relevancy_keywords.txt.tmp')  # noqa


def get_relevancy_keywords():
    keywords_filepath = RELEVANCY_KEYWORDS_FILEPATH
    keywords_out = []

    if os.path.exists(keywords_filepath):
        with open(keywords_filepath, 'rb') as kf:
            for line in kf:
                keywords_out.append(line.decode('UTF-8').strip())
            kf.close()
    return keywords_out


RELEVANCY_KEYWORDS = get_relevancy_keywords()

SR_CALCULATE = False
# new SR must differ by SR_MIN_DIFF points from the old one
# if the old one was set
SR_MIN_DIFF = 10.0
SR_WEIGHT_COMMENT_NUMBER = 2.0
SR_WEIGHT_LIKEVOTE_NUMBER = 1.0
SR_WEIGHT_DRANK_IT_TOO_NUMBER = 1.5
SR_WEIGHT_DESCRIPTION_LENGTH = 0.1
SR_WEIGHT_RELEVANCY_KEYWORD = 0.5
SR_WEIGHT_IMAGE = 1.0
SR_MIN_POINTS_COMMENT_NUMBER = 2.0
SR_MIN_POINTS_LIKEVOTE_NUMBER = 4.0
SR_MIN_POINTS_DRANK_IT_TOO_NUMBER = 4.0
SR_MIN_POINTS_DESCRIPTION_LENGTH = 10
SR_MIN_POINTS_RELEVANCY = 0.5
SR_MIN_DESCRIPTION_LENGTH = 300
SR_STRATEGY_MIN_INDIVIDUAL_POINTS = 'individual_points'
SR_STRATEGY_MIN_TOTAL_POINTS = 'total_points'
SR_STRATEGY = SR_STRATEGY_MIN_TOTAL_POINTS
SR_MIN_TOTAL_POINTS = 7.50
MOVE_PARENT_POSTS_ON_APP_DELETE = True
ADMIN_PROFILE_USERNAME = 'admin-profile'
