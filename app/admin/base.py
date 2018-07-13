from flask import g
from flask_admin import BaseView
from flask_admin.contrib.mongoengine import ModelView


class AuthView(BaseView):
    def is_accessible(self):
        #res = g.user.is_authenticated
        return True


class AuthModelView(ModelView):
    column_exclude_list = ['extra_data', 'created_at', 'updated_at']

    def is_accessible(self):
        #res = g.user.is_authenticated
        return True
