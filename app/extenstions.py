#!usr/bin/env python
# -*- coding: utf-8 -*-
from flask_admin import Admin
from flask_mongoengine import MongoEngine

from app.admin.manual_cron import ManualCronView

admin = Admin(index_view=ManualCronView(), template_mode='bootstrap3')
db = MongoEngine()