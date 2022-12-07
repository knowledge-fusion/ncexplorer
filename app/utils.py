import os
from ast import literal_eval

from flask import current_app
from flask_admin.contrib.mongoengine import filters

from app.config import DefaultConfig
from app.extenstions import cache


# pylint: disable=protected-access
def get_config(key):
    result = None
    try:
        result = current_app.config.get(key)
    except RuntimeError:
        result = getattr(DefaultConfig, key)
    return result


def shorten_url(url):
    res = url.split("/")[-1]
    if url.startswith("http://dbpedia.org/ontology/"):
        res = "dbo:%s" % url.split("http://dbpedia.org/ontology/")[1]
    elif url.startswith("http://dbpedia.org/class/yago/"):
        res = "yago:%s" % url.split("http://dbpedia.org/class/yago/")[1]
    elif url.startswith("http://dbpedia.org/resource/"):
        res = "DBpedia:%s" % url.split("http://dbpedia.org/resource/")[1]
    elif url.startswith("http://www.w3.org/2000/01/rdf-schema#"):
        res = "rdfs:%s" % url.split("http://www.w3.org/2000/01/rdf-schema#")[1]
    elif url.startswith("http://www.w3.org/1999/02/22-rdf-syntax-ns#"):
        res = "rdf:%s" % url.split("http://www.w3.org/1999/02/22-rdf-syntax-ns#")[1]
    elif url.startswith("http://dbpedia.org/resource/Category:"):
        res = "dbc:%s" % url.split("http://dbpedia.org/resource/Category:")[1]
    elif url.startswith("http://dbpedia.org/property/"):
        res = "dbp:%s" % url.split("http://dbpedia.org/property/")[1]
    else:
        res = "other:%s" % url.split("/")[-1]
    return res


def init_celery(app, celery):
    """Add flask app context to celery.Task"""
    from celery_singleton import Singleton

    class ContextTask(Singleton):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return Singleton.__call__(self, *args, **kwargs)

    celery.Task = ContextTask

    import sentry_sdk
    from sentry_sdk.integrations.celery import CeleryIntegration

    sentry_sdk.init(
        dsn=app.config["SENTRY_DSN"],
        environment=app.config["SENTRY_ENVIRONMENT"],
        integrations=[CeleryIntegration()],
    )


@cache.memoize(timeout=None)
def get_remote_template(url):
    import requests

    try:
        resp = requests.get(url)
        return resp.text if resp.status_code == 200 else None
    except Exception:
        return None


def cache_api_response(backend, end_point, content):
    if get_config("CACHE_API_RESPONSE"):
        import responses

        mock_disabled = hasattr(responses.mock, "_patcher") and len(
            responses.mock._patcher._active_patches
        )
        mock_disabled = True

        if mock_disabled:
            basepath = os.path.dirname(__file__)
            path = current_app.config["API_RESPONSE_CACHE_DIR"] % (backend, end_point)
            filepath = os.path.abspath(os.path.join(basepath, path))
            with open(filepath, "w") as f:
                f.write(content)
                f.close()


def graceful_auto_reconnect(mongo_op_func):
    """Gracefully handle a reconnection event."""

    import functools
    import logging
    import time

    import pymongo

    @functools.wraps(mongo_op_func)
    def wrapper(*args, **kwargs):
        for attempt in range(5):
            try:
                return mongo_op_func(*args, **kwargs)
            except pymongo.errors.AutoReconnect as e:
                wait_t = 0.5 * pow(2, attempt)  # exponential back off
                logging.warning(
                    "PyMongo auto-reconnecting... %s. Waiting %.1f seconds.",
                    str(e),
                    wait_t,
                )
                time.sleep(wait_t)

    return wrapper


def chunks(lst, size):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(lst), size):
        yield lst[i : i + size]


def flask_admin_select_filter(column):
    def _options():
        try:
            """
            results = column.owner_document.objects.distinct(field=column.name)
            items = [(item, item) for item in results]
            """
            return []
        except Exception:
            return []

    return filters.FilterEqual(column, column.name, options=_options)


def config_from_env_vars(prefix=""):
    _SECRET_KEYWORDS = ("pass", "secret", "token")

    def _mask_secret(name, value):
        name = name.lower()
        for keyword in _SECRET_KEYWORDS:
            if keyword in name:
                return "********"
        return value

    results = {}
    for k, v in os.environ.items():
        if k.startswith(prefix):
            k = k[len(prefix) :]
            try:
                v = literal_eval(v)
            except (ValueError, SyntaxError):
                pass
            results[k] = v
            print(
                'override config from environment: "{}" = "{}"'.format(
                    k, _mask_secret(k, v)
                )
            )
    return results


def get_enum_choices(enum):
    return tuple((e.value, e.name) for e in enum)


def get_enum_values(enum):
    return tuple(e.value for e in enum)


def is_valid_abstraction(abstraction):
    valid = abstraction.find("missing") == -1
    valid &= abstraction.find("_births") == -1
    valid &= abstraction.find("_deaths") == -1
    valid &= abstraction.lower().find("articles") == -1
    valid &= abstraction.find("http://dbpedia.org/class/yago/") == -1
    valid &= abstraction.lower().find("unprintworthy_redirects") == -1
    valid &= abstraction.find("Category:WikiProjects") == -1
    valid &= abstraction.find("Category:Wikipedia") == -1
    valid &= abstraction.find("_stubs") == -1
    valid &= abstraction.find("_templates") == -1
    valid &= abstraction.find("cleanup") == -1
    valid &= abstraction.find("unknown") == -1
    valid &= abstraction.find("pages") == -1

    return valid


def cosine_similarity(a, b):
    from numpy import inner
    from numpy.linalg import norm

    res = inner(a, b) / (norm(a) * norm(b))
    return res


def power_set(s, size_limit=None):
    if not size_limit:
        size_limit = len(s)
    if len(s) < size_limit:
        size_limit = len(s)
    res = []
    for i in range(1 << size_limit):
        res += [s[j] for j in range(size_limit) if (i & (1 << j))]
    return res
