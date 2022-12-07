#!/usr/bin/env python

from app.application import create_app

app = create_app()
app.app_context().push()
