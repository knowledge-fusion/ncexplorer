#!usr/bin/env python

import flask_login

# from celery import Celery
from flask import (
    Flask,
    current_app,
    g,
    make_response,
    redirect,
    render_template,
    request,
)
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix

from app.commandline import configure_commandline
from app.common.mongoengine_base import BaseDocument
from app.config import DefaultConfig
from app.extenstions import admin, cache, db
from app.utils import config_from_env_vars
from app.views.news_search import services as news_search_blueprint
from app.views.pattern_explore import related_term
from app.views.pattern_explore import services as search_pattern_bluprint
from app.views.pattern_explore import trending_patterns

__all__ = ["create_app"]

DEFAULT_BLUEPRINTS = [search_pattern_bluprint, news_search_blueprint]

# celery = Celery(__name__, config_source=DefaultConfig)


# pylint: disable=unused-argument,unused-variable


def create_app(config=None, app_name=None, blueprints=None):
    """Create a Flask app."""

    if app_name is None:
        app_name = DefaultConfig.PROJECT
    if blueprints is None:
        blueprints = DEFAULT_BLUEPRINTS

    app = Flask(app_name, instance_relative_config=True)
    app.wsgi_app = ProxyFix(app.wsgi_app)

    configure_app(app, config)
    configure_logging(app)
    configure_blueprints(app, blueprints)
    configure_extensions(app)
    configure_signals(app)
    configure_error_handlers(app)
    configure_commandline(app)

    return app


def configure_logging(app):
    import sentry_sdk
    from sentry_sdk.integrations.aws_lambda import (
        AwsLambdaIntegration,
        get_lambda_bootstrap,
    )
    from sentry_sdk.integrations.flask import FlaskIntegration

    if get_lambda_bootstrap():
        integrations = [FlaskIntegration(), AwsLambdaIntegration(timeout_warning=True)]
        sentry_sdk.init(
            dsn=app.config["SENTRY_DSN"],
            environment=app.config["SENTRY_ENVIRONMENT"],
            integrations=integrations,
        )


def configure_app(app, config=None):
    """Different ways of configurations."""

    # http://flask.pocoo.org/docs/api/#configuration
    if config:
        app.config.from_object(config)
    else:
        app.config.from_object(DefaultConfig)
    app.config.update(config_from_env_vars("NLP_"))


def configure_extensions(app):
    # flask-mongoengine
    db.init_app(app)
    db.Document = BaseDocument

    # from flask_compress import Compress
    #
    # compress = Compress()
    # compress.init_app(app)

    # cors
    CORS(app, resources={r"/*": {"origins": "*"}})

    import redis

    app.redis = redis.Redis.from_url(
        app.config["REDIS_URL"],
        socket_timeout=5,
        socket_connect_timeout=5,
    )

    try:
        print(app.redis.ping())
    except Exception:
        import os

        print("redis not available")
        app.config["CACHE_TYPE"] = "FileSystemCache"
        app.config["CACHE_DIR"] = os.path.dirname(__file__) + "/../.cache"
        print(app.config["CACHE_DIR"])
    # cache
    cache.init_app(app)
    cache.add("foo", "bar")

    # admin
    if app.config["ENABLE_ADMIN_VIEW"]:
        try:
            from app.admin.views import add_admin_views

            admin.init_app(app)
            add_admin_views(admin)
        except AssertionError as e:
            print(e)

    login_manager = flask_login.LoginManager()
    login_manager.init_app(app)

    @login_manager.user_loader
    def user_loader(username):
        if username != current_app.config["ADMIN_USERNAME"]:
            return None
        user = flask_login.UserMixin()
        user.id = username
        return user

    login_manager.login_view = "admin.index"

    @app.route("/favicon.ico", methods=["GET"])
    def favicon():
        return app.send_static_file("favicon.ico")

    @app.route("/", methods=["GET", "POST"])
    def index():
        if request.method == "POST":
            username = request.form.get("username")
            if request.form.get("pw") == current_app.config["ADMIN_PASSWORD"]:
                user = flask_login.UserMixin()
                user.id = username
                flask_login.login_user(user)
                redirect_url = request.args.get("next") or "/admin/"
                return redirect(redirect_url)

        return render_template("index.html")

    @app.route("/data_migration")
    def data_migration_view():
        from app.commandline import data_migration

        data_migration()
        return "OK"

    @app.route("/logout")
    def logout():
        flask_login.logout_user()
        g.user = None
        return redirect("/")

    # from app.similarity.dbpedia_dump_utils import dbpedia_ontology_graph
    # app.ontology_graph = dbpedia_ontology_graph()
    # healthcheck
    from healthcheck import HealthCheck

    health = HealthCheck(app, "/healthcheck")

    import os

    from app.views.internal_healthcheck import check_s3_data_backup_ok, mongo_available

    filename = os.path.dirname(os.path.realpath(__file__)) + "/../setup.py"

    def report_version():
        version = None
        with open(filename) as f:
            for line in f:
                if line.startswith("__version__"):
                    _, version, _ = line.split('"')
                    break
        return True, {"version": version}

    health.add_check(mongo_available)
    health.add_check(check_s3_data_backup_ok)
    health.add_check(report_version)

    # health.add_check(cron_task_scheduler_status_ok)

    @app.route("/similar")
    def similar_news(news_id=None):
        return render_template("similar.html")


def configure_signals(app):
    pass


def configure_blueprints(app, blueprints):
    """Configure blueprints in views."""

    for blueprint in blueprints:
        app.register_blueprint(blueprint)

    @app.route("/reset_cache")
    def reset_cache():
        from app.utils import get_remote_template

        cache.delete_memoized(trending_patterns)
        cache.delete_memoized(related_term)
        cache.delete_memoized(get_remote_template)
        return make_response("OK", 200)


def configure_error_handlers(app):
    @app.errorhandler(Exception)
    def handle_error(error):
        app.logger.exception(error)
        return redirect("/")

    @app.errorhandler(403)
    def forbidden_page(error):
        return redirect("/")

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def server_error_page(error):
        current_app.logger.exception(error)
        return redirect("/")


if __name__ == "__main__":
    application = create_app()
    application.run(debug=True, host="0.0.0.0", port=5100, threaded=True)
