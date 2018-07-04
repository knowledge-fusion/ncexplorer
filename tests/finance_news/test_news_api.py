import os

import responses
from mongoengine import Q

from app.finance_news.fetch import fetch_symbol
from app.finance_news.models import FinanceNews
from app.finance_news.providers.newsriver import init


def test_query_news(mock_news_api):
    #responses.start()
    results = fetch_symbol(publisher='ft.com', provider='newsriver', token=os.getenv(
        'NEWS_RIVER0'))
    pass
    #responses.stop()