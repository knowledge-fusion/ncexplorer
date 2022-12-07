import pytest

from app.application import create_app
from app.config import TestConfig
from app.models.news_analytics import NewsAnalytics


@pytest.fixture(autouse=True, scope="session")
def app(request):
    """
    Test app
    """
    application = create_app(TestConfig)
    # application.test_client_class = TestClient

    ctx = application.app_context()
    ctx.push()

    def teardown():
        print("tear down %s" % ctx)
        # db.connection.drop_database(db.connection.get_default_database().name)
        ctx.pop()

    request.addfinalizer(teardown)
    return application


@pytest.fixture(scope="module")
def celery_app(request):
    DEFAULT_TEST_CONFIG = {
        "worker_hijack_root_logger": False,
        "worker_log_color": False,
        "accept_content": {"json"},
        "enable_utc": True,
        "timezone": "UTC",
        "broker_url": "memory://",
        "result_backend": "cache+memory://",
        "broker_heartbeat": 0,
    }
    celery.conf.update(DEFAULT_TEST_CONFIG)
    return celery


@pytest.fixture
def test_news_url():
    url = "20150302-060000000-nL1N0W30NB-1-2"
    return url


@pytest.fixture
def test_news_analytics(test_news_url):
    test_news_analytics = NewsAnalytics.objects(url=test_news_url).first()
    return test_news_analytics
