#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

from flask import current_app
from flask_script import Manager, Shell

from app.application import create_app
from app.config import ManageConfig


def _shell_context():
    ctx = {
        'app': current_app,
    }
    print 'loaded context', ctx
    return ctx


manager = Manager(create_app(ManageConfig))
manager.add_command('shell', Shell(make_context=_shell_context))
#db_manager = Manager(create_app(ManageConfig))
#manager.add_command('db', db_manager)


@manager.command
def urls():
    print 'urls on tac:'
    for rule in current_app.url_map.iter_rules():
        if rule.endpoint != 'static' and rule.rule.find('/admin/') < 0:
            print '%s  =>  %s' % (rule.endpoint, rule.rule)


@manager.option('-k', '--key', dest='key')
@manager.option('-s', '--secret', dest='secret')
@manager.option('-p', '--path', dest='path')
@manager.option('-m', '--only_modified', dest='only_modified')
def distribute_static_assets(key, secret, path, only_modified):
    print 'this does not work for uploading templates, only upload files in static directory'
    print 'distribute static %s assets to aws s3. only modified %s' % (path, only_modified)
    import flask_s3
    current_app.config['FLASKS3_ONLY_MODIFIED'] = only_modified
    flask_s3.create_all(current_app, user=key,
                        password=secret,
                        filepath_filter_regex=r'^templates')

'''
@db_manager.command
def data_migration_cli():
    # pylint: disable=protected-access,too-many-locals,invalid-name,pointless-string-statement
    # update to new scopes
    res = 'ok'

    return res
'''

if __name__ == "__main__":
    manager.run(default_command='urls')
