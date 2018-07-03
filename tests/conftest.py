import pytest

from app.application import create_app, celery
from app.config import TestConfig


@pytest.fixture(autouse=True, scope='session')
def app(request):
    """
    Test app
    """
    application = create_app(TestConfig)
    #application.test_client_class = TestClient
    celery.conf.task_always_eager = True

    ctx = application.app_context()
    ctx.push()

    def teardown():
        print('tear down %s' % ctx)
        #db.connection.drop_database(db.connection.get_default_database().name)
        ctx.pop()

    request.addfinalizer(teardown)
    return application


@pytest.fixture(scope='module')
def celery_app(request):
    DEFAULT_TEST_CONFIG = {
        'worker_hijack_root_logger': False,
        'worker_log_color': False,
        'accept_content': {'json'},
        'enable_utc': True,
        'timezone': 'UTC',
        'broker_url': 'memory://',
        'result_backend': 'cache+memory://',
        'broker_heartbeat': 0,
    }
    celery.conf.update(DEFAULT_TEST_CONFIG)
    return celery