from pymongo import UpdateOne

from app.finance_news.models import SyncStatus, Stock
from app.tasks import intrinio_company_news


def test_init_sync_status(app, intrinio_fetcher):
    res = SyncStatus.objects(provider='intrinio', offset=None).update(set__offset=0)
    publisher = 'company_news'
    provider = intrinio_fetcher.name
    symbols = Stock.objects.distinct('symbol')
    operations = []
    for symbol in symbols:
        if not any(char.isdigit() for char in symbol):
            updates = {'symbol': symbol, 'provider': provider, 'publisher': publisher, 'offset':
                0, 'has_more': True}
            operations.append(UpdateOne({'symbol': symbol, 'provider': provider, 'publisher':
                publisher}, {'$set': updates}, upsert=True))

    if operations:
        SyncStatus._get_collection().bulk_write(operations, ordered=False)


def test_fetch_company(app, intrinio_fetcher):
    intrinio_fetcher.fetch_companies()


def test_fetch_economic_indices(app, intrinio_fetcher):
    intrinio_fetcher.intrinio.client.cache_enabled = False
    intrinio_fetcher.fetch_economic_indices()


def test_fetch_company_news(app, intrinio_fetcher):

    intrinio_company_news()
