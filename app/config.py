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
    broker_url = (os.getenv('CELERY_BROKER_URL') or os.getenv('REDIS_PORT_6379_TCP_ADDR') or 'redis://localhost')
    result_backend = (os.getenv('CELERY_BROKER_URL') or os.getenv('REDIS_PORT_6379_TCP_ADDR') or 'redis://localhost')
    enable_utc = True
    worker_hijack_root_logger = False
    worker_log_color = False
    task_ignore_result = False
    beat_schedule = {
        'watson_analytics': {
            'task': 'tasks.watson_analytics',
            'schedule': timedelta(minutes=1.3),
        },
        #'stock_daily_timeseries': {
        #    'task': 'tasks.stock_daily_timeseries_data',
        #    'schedule': timedelta(minutes=1)
        #},
        #'newsriver_fetch_update': {
        #    'task': 'tasks.fetch_newsriver_update',
        #    'schedule': timedelta(minutes=16)
        #},
        'intrinio-news': {
            'task': 'tasks.intrinio_company_news',
            'schedule': timedelta(minutes=5)
        }
    }
    broker_transport_options = {'visibility_timeout': 60}  # 1 minute.

    CELERY_GEVENT_POOL_SIZE = 20
    #redis_max_connections = 5


class DefaultConfig(CeleryConfig):
    DEBUG = True
    PROJECT = 'natural-language-understanding'
    ENABLE_ADMIN_VIEW = True
    MONGODB_HOST = os.getenv('MONGODB_HOST')
    SENTRY_DSN = os.getenv('SENTRY_DSN')
    SENTRY_LOG_LEVEL = logging.ERROR
    SECRET_KEY = os.getenv('SECRET_KEY')

    # LOGIN
    ADMIN_USERNAME = os.getenv('ADMIN_USERNAME')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')

    # WATSON
    WATSON_VERSION = os.getenv('WATSON_VERSION')

    # flask-s3
    FLASKS3_BUCKET_NAME = 'natual-language-processing-static-assets'
    FLASKS3_FORCE_MIMETYPE = True
    FLASKS3_ONLY_MODIFIED = True
    REMOTE_TEMPLATE_BASE_URL = 'https://s3-ap-southeast-1.amazonaws.com/natual-language' \
                               '-processing-static-assets/templates/'


class ManageConfig(DefaultConfig):
    ENABLE_ADMIN_VIEW = True


class TestConfig(DefaultConfig):
    TESTING = True
    CACHE_API_RESPONSE = True
    API_RESPONSE_CACHE_DIR = '../tests/finance_news/data/%s/%s'
