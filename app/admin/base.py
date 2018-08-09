from flask_admin import BaseView
from flask_admin.contrib.mongoengine import ModelView
from flask_login import login_required


class AuthView(BaseView):
    @login_required
    def is_accessible(self):
        return True


class AuthModelView(ModelView):
    column_exclude_list = ['extra_data', 'created_at', 'updated_at']

    @login_required
    def is_accessible(self):
        return True
