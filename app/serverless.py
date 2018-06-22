# coding=utf-8
# pylint: disable=invalid-name,redefined-outer-name

from app.application import create_app

app = create_app()


def unhandled_exception(e, event, context):
    from raven import Client
    client = Client(app.config['SENTRY_DSN'])
    client.capture(e, data=event, extra={
        'context': context,
        'e': e,
        'event': event
    })
    return True
