from flask_admin import BaseView
from flask_admin.contrib.mongoengine import ModelView


class AuthView(BaseView):
    def is_accessible(self):
        from flask_login import current_user
        res = current_user.is_authenticated


class AuthModelView(ModelView):
    column_exclude_list = ['extra_data', 'created_at', 'updated_at']

    def is_accessible(self):
        from flask_login import current_user
        res = current_user.is_authenticated
        return res
