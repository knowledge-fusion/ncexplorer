import os
from datetime import timedelta

from dotenv import load_dotenv, find_dotenv
import logging

load_dotenv(find_dotenv())



class CeleryConfig(object):
    # celery config, user lower case for celery >= 4.0
    # Note, lower case config is not registered with flask.config object
    # manual configuration is expected
    # http://docs.celeryproject.org/en/latest/userguide/configuration.html#configuration
    # http://flask.pocoo.org/docs/0.12/config/
    broker_url = (os.getenv('CELERY_BROKER_URL') or 'redis://localhost')
    result_backend = (os.getenv('CELERY_BROKER_URL') or 'redis://localhost')
    enable_utc = True
    worker_hijack_root_logger = False
    worker_log_color = False
    task_ignore_result = False
    beat_schedule = {
        'fitbit-sync': {
            'task': 'tasks.watson_analytics',
            'schedule': timedelta(minutes=5),
        }
    }

    CELERY_GEVENT_POOL_SIZE = 20

class DefaultConfig(CeleryConfig):
    DEBUG = True
    PROJECT = 'natual-language-understanding'
    ENABLE_ADMIN_VIEW = True
    MONGODB_HOST = os.getenv('MONGODB_HOST')
    SENTRY_DSN = os.getenv('SENTRY_DSN')
    SENTRY_LOG_LEVEL = logging.ERROR
    SECRET_KEY = os.getenv('SECRET_KEY')

    #LOGIN
    ADMIN_USERNAME = os.getenv('ADMIN_USERNAME')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')

    # WATSON
    WATSON_VERSION = '2018-03-16'
    WATSON_USERNAME = os.getenv('WATSON_USERNAME')
    WATSON_PASSWORD = os.getenv('WATSON_PASSWORD')


class TestConfig(DefaultConfig):
    TESTING = True
