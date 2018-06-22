#!usr/bin/env python
# -*- coding: utf-8 -*-
from flask import Flask, g, redirect, request, flash, current_app, \
    url_for, render_template
from flask import make_response
from raven.contrib.flask import Sentry
from raven.handlers.logging import SentryHandler
from werkzeug.contrib.fixers import ProxyFix



from app.common.mongoengine_base import BaseDocument
from app.config import DefaultConfig
from app.extenstions import admin, db

DEFAULT_BLUEPRINTS = []


def create_app(config=None, app_name=None, blueprints=None):
    """Create a Flask app."""

    if app_name is None:
        app_name = DefaultConfig.PROJECT
    if blueprints is None:
        blueprints = DEFAULT_BLUEPRINTS

    app = Flask(app_name, instance_relative_config=True)
    app.wsgi_app = ProxyFix(app.wsgi_app, num_proxies=2)

    configure_app(app, config)
    configure_logging(app)
    configure_blueprints(app, blueprints)
    configure_extensions(app)
    configure_signals(app)
    configure_error_handlers(app)

    return app


def configure_logging(app):
    if not app.config['DEBUG']:
        sentry = Sentry(app, dsn=app.config['SENTRY_DSN'])
        handler = SentryHandler(client=sentry.client, level=app.config['SENTRY_LOG_LEVEL'])
        app.logger.addHandler(handler)


def configure_app(app, config=None):
    """Different ways of configurations."""

    # http://flask.pocoo.org/docs/api/#configuration
    if config:
        app.config.from_object(config)
    else:
        app.config.from_object(DefaultConfig)


def configure_extensions(app):
    # flask-mongoengine
    db.init_app(app)
    db.Document = BaseDocument

    # admin
    if app.config['ENABLE_ADMIN_VIEW']:
        try:
            from app.admin.views import add_admin_views
            admin.init_app(app)
            add_admin_views(admin)
        except AssertionError as e:
            if app.testing:
                print "A blueprint's name collision, happended during test", e
            else:
                raise


def configure_signals(app):
    pass


def configure_blueprints(app, blueprints):
    """Configure blueprints in views."""

    for blueprint in blueprints:
        app.register_blueprint(blueprint)

    @app.route('/')
    def index():
        return "hello world", 200

def configure_error_handlers(app):
    @app.errorhandler(Exception)
    def handle_error(error):
        app.logger.exception(error)
        return redirect('/')

    @app.errorhandler(403)
    def forbidden_page(error):
        return redirect('/')

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def server_error_page(error):
        current_app.logger.exception(error)
        return redirect('/')

if __name__ == '__main__':
    application = create_app()
    application.run(debug=True, host='0.0.0.0', port=5100, threaded=True)
