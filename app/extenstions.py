#!usr/bin/env python
# -*- coding: utf-8 -*-
from flask_admin import Admin
from flask_mongoengine import MongoEngine

admin = Admin(template_mode='bootstrap3')
db = MongoEngine()