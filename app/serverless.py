def unhandled_exception(exception, event, context):
    import sentry_sdk

    sentry_sdk.init(
        dsn="https://65725ec727d34974a4672fa768d82dad@o153177.ingest.sentry.io/1205986",
        environment="dev",
    )
    with sentry_sdk.configure_scope() as scope:
        scope.set_extra("event", event)
        scope.set_extra("context", context)
        sentry_sdk.capture_exception(exception)
    return True


from app.application import create_app

app = create_app()
