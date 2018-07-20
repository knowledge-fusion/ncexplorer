import os

from app.finance_news.fetch import fetch_symbol
from app.tasks import intrinio_company_news


def test_intrinio_company_news(app):
    intrinio_company_news()

def test_query_news(mock_news_api):
    #responses.start()
    results = fetch_symbol(publisher='ft.com', provider='newsriver', token=os.getenv(
        'NEWS_RIVER0'))
    pass
    #responses.stop()