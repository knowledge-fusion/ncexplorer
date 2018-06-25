import os

from dotenv import load_dotenv, find_dotenv
import logging

load_dotenv(find_dotenv())


class DefaultConfig(object):
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
