import responses
from mongoengine import Q

from app.finance_news.fetch import fetch_symbol
from app.finance_news.models import FinanceNews
from app.finance_news.providers.newsriver import init


def test_query_news(mock_news_api):
    #responses.start()
    fetch_symbol(publisher='seekingalpha.com', provider='newsriver')
    #responses.stop()