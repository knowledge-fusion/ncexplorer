import pytest

from app.application import create_app
from app.config import TestConfig


@pytest.fixture(autouse=True, scope='session')
def app(request):
    """
    Test app
    """
    application = create_app(TestConfig)
    #application.test_client_class = TestClient

    ctx = application.app_context()
    ctx.push()

    def teardown():
        print('tear down %s' % ctx)
        #db.connection.drop_database(db.connection.get_default_database().name)
        ctx.pop()

    request.addfinalizer(teardown)
    return application