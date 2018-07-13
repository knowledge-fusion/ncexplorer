#!usr/bin/env python
# -*- coding: utf-8 -*-
import flask_login
from celery import Celery
from flask import Flask, redirect, request, current_app, \
    jsonify, make_response, g
from flask_login import UserMixin, LoginManager
from raven.contrib.flask import Sentry
from raven.handlers.logging import SentryHandler
from werkzeug.contrib.fixers import ProxyFix

from app.common.mongoengine_base import BaseDocument
from app.config import DefaultConfig
from app.extenstions import admin, db, cache
from app.utils import render

__all__ = ['create_app', 'celery']

DEFAULT_BLUEPRINTS = []

celery = Celery(__name__, config_source=DefaultConfig)


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

    # cache
    cache.init_app(app)

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

    login_manager = LoginManager()
    login_manager.init_app(app)

    class User(UserMixin):
        pass

    @login_manager.user_loader
    def user_loader(username):
        if username != current_app.config['ADMIN_USERNAME']:
            return None
        user = User()
        user.id = username
        return user

    @login_manager.request_loader
    def request_loader(req):
        username = req.form.get('username')
        if username != current_app.config['ADMIN_USERNAME']:
            return None

        user = User()
        user.id = username
        return user

    login_manager.login_view = "index"

    @app.route('/', methods=['GET', 'POST'])
    def index():

        return redirect('/admin/')

        if request.method == 'POST':
            username = request.form.get('username')
            if request.form.get('pw') == current_app.config['ADMIN_PASSWORD']:
                user = User()
                user.id = username
                flask_login.login_user(user)
                g.user = user
                redirect_url = request.args.get('next') or '/admin/'
                return redirect(redirect_url)
        return render('index.html')

    @app.route('/admin')
    def admin_redirect():
        return redirect('/admin/')

    @app.route('/logout')
    def logout():
        flask_login.logout_user()
        g.uesr = None
        return redirect('/')


def configure_signals(app):
    pass


def configure_blueprints(app, blueprints):
    """Configure blueprints in views."""

    for blueprint in blueprints:
        app.register_blueprint(blueprint)

    @app.route('/reset_cache')
    def reset_cache():
        from app.utils import get_remote_template
        cache.delete_memoized(get_remote_template)
        return make_response("OK", 200)

    @app.route('/task_status/<string:task_id>/', methods=['GET'])
    def task_status(task_id):
        task = celery.AsyncResult(task_id)
        response = {
            'state': task.state,
            'status': task.status,
            'result': str(task.info),
            'ready': task.ready(),
            'successful': task.successful()
        }
        if task.children and task.children and isinstance(task.children[0],
                                                          celery.GroupResult):
            response['ready'] = task.children[0].ready()
            response['successful'] = task.children[0].successful()

        return jsonify(response)


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
        return render('404.html'), 404

    @app.errorhandler(500)
    def server_error_page(error):
        current_app.logger.exception(error)
        return redirect('/')


if __name__ == '__main__':
    application = create_app()
    application.run(debug=True, host='0.0.0.0', port=5100, threaded=True)
