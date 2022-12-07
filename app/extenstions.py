#!usr/bin/env python
from flask_admin import Admin, AdminIndexView
from flask_caching import Cache
from flask_mongoengine import MongoEngine

admin = Admin(index_view=AdminIndexView(), template_mode="bootstrap3")
db = MongoEngine()
cache = Cache()
