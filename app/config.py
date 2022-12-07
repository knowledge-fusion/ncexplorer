import os
from datetime import timedelta

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(filename=".env", raise_error_if_not_found=True, usecwd=True))


class CeleryConfig:
    # celery config, user lower case for celery >= 4.0
    # Note, lower case config is not registered with flask.config object
    # manual configuration is expected
    # http://docs.celeryproject.org/en/latest/userguide/configuration.html#configuration
    # http://flask.pocoo.org/docs/0.12/config/
    broker_url = os.getenv(
        "CELERY_BROKER_URL",
        "redis://%s:6379" % os.getenv("REDIS_PORT_6379_TCP_ADDR", "localhost"),
    )
    result_backend = os.getenv(
        "CELERY_BROKER_URL",
        "redis://%s:6379" % os.getenv("REDIS_PORT_6379_TCP_ADDR", "localhost"),
    )
    singleton_backend_url = broker_url
    enable_utc = True
    worker_hijack_root_logger = False
    worker_log_color = False
    task_ignore_result = False
    beat_schedule = {
        #'generate_market_event': {
        #    'task': 'tasks.generate_market_event',
        #    'schedule': timedelta(hours=1)
        # },
        "update_counter_task": {
            "task": "tasks.update_counter_task",
            "schedule": timedelta(minutes=5),
        },
        # "task_process_reuters_news": {
        #    "task": "app.news_importer.tasks.task_process_reuters_news",
        #    "schedule": timedelta(minutes=5),
        # },
        # "task_process_seekingalpha_news": {
        #    "task": "app.news_importer.tasks.task_process_seekingalpha_news",
        #    "schedule": timedelta(minutes=5),
        # },
        # "task_fetch_nyt_news": {
        #    "task": "app.news_importer.tasks.task_fetch_nyt_news",
        #    "schedule": crontab(day_of_month=2),
        # },
        # "task_reanalyze_news": {
        #    "task": "app.news_processor.tasks.task_analyze_news",
        #    "schedule": timedelta(minutes=5),
        # },
        # "refresh_connected_component": {
        #    "task": "app.news_processor.tasks.refresh_connected_component",
        #    "schedule": timedelta(minutes=5),
        # },
        # "calculate_news_abstraction_task": {
        #    "task": "tasks.adhoc_task_master",
        #    "schedule": timedelta(minutes=5),
        # },
        # "task_calculate_abstraction": {
        #    "task": "app.association_rules.tasks.calculate_entity_abstraction_task",
        #    "schedule": timedelta(minutes=5),
        # },
        # "refresh_wikidata_entity_tuple": {
        #    "task": "app.news_processor.tasks.refresh_wikidata_entity_tuple",
        #    "schedule": timedelta(minutes=5),
        # }
        # "adhoc_task": {
        #    "task": "tasks.adhoc_task",
        #    "schedule": timedelta(minutes=5),
        # },
        # "adhoc_task3": {
        #    "task": "tasks.adhoc_task_master",
        #    "schedule": timedelta(minutes=5),
        # },
    }
    broker_transport_options = {"visibility_timeout": 2}  # 1 minute.

    CELERY_GEVENT_POOL_SIZE = 20
    # redis_max_connections = 5


class DefaultConfig(CeleryConfig):
    DEBUG = True
    PROJECT = "app"
    ENABLE_ADMIN_VIEW = True
    FLASK_ADMIN_SWATCH = "paper"
    COMPRESS_ALGORITHM = ["gzip", "deflate"]
    NEL_ENDPOINT = "http://nel:nel@%s:5200/api" % os.getenv(
        "NEL_PORT_5200_TCP_ADDR", os.getenv("NEL_HOST")
    )
    MONGODB_HOST = "mongodb://%s:27017/finance" % os.getenv(
        "MONGODB_PORT_27017_TCP_ADDR", "localhost"
    )

    # LOGIN
    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

    # DBPedsudo ia
    DBPEDIA_BASE_URL = os.getenv(
        "DBPEDIA_BASE_URL", "http://%s:80/rest" % os.getenv("DBPEDIA_PORT_80_TCP_ADDR")
    )

    ALPHAVANTAGE_API_KEY = os.getenv("ALPHAVANTAGE_API_KEY")
    # flask-s3
    FLASKS3_BUCKET_NAME = "natual-language-processing-static-assets"
    FLASKS3_FORCE_MIMETYPE = True
    FLASKS3_ONLY_MODIFIED = True
    REMOTE_TEMPLATE_BASE_URL = (
        "https://s3-ap-southeast-1.amazonaws.com/natual-language"
        "-processing-static-assets/templates/"
    )
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

    # flask-cache
    CACHE_TYPE = "RedisCache"
    CACHE_REDIS_DB = 4
    CACHE_REDIS_PASSWORD = os.getenv("NLP_REDIS_PASSWORD")
    ABSTRACT_TYPE_DELIMITER = "&&"
    DBPEDIA_PREFIX = "http://dbpedia.org/resource/"


class ManageConfig(DefaultConfig):
    ENABLE_ADMIN_VIEW = True


class TestConfig(DefaultConfig):
    TESTING = True
    CACHE_API_RESPONSE = True
    API_RESPONSE_CACHE_DIR = "../tests/news_importer/data/%s/%s"
