#!/usr/bin/env python
import os
from app.application import create_app
from app.tasks import celery

app = create_app()
app.app_context().push()
