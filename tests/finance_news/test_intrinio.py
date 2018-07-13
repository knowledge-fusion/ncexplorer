import datetime


def test_fetch_company(app, intrinio_fetcher):
    intrinio_fetcher.fetch_companies()


def test_fetch_economic_indices(app, intrinio_fetcher):
    intrinio_fetcher.intrinio.client.cache_enabled = False
    intrinio_fetcher.fetch_economic_indices()


def test_fetch_company_news(app, intrinio_fetcher):
    intrinio_fetcher.intrinio.client.cache_enabled = False
    intrinio_fetcher.fetch_company_news('AAPL')

