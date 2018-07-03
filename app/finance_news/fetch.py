from datetime import datetime

from pymongo import UpdateOne

from app.finance_news.models import FinanceNews, SyncStatus
from app.finance_news.providers.newsriver import query_news_update


def fetch_symbol(provider, publisher):
    status = SyncStatus.objects(provider=provider, publisher=publisher).first()
    if not status.timestamp:
        status.timestamp = datetime.fromtimestamp(1511675881)
    results = query_news_update(publisher=status.publisher, date=status.timestamp)
    operations = []
    for result in results:
        operations.append(UpdateOne({'url': result['url']}, {'$set': result},
                                    upsert=True))
        status.timestamp = datetime.fromtimestamp(result['timestamp'])
    status.last_sync_operation = datetime.utcnow()
    status.save()
    if operations:
        FinanceNews._get_collection().bulk_write(operations, ordered=False)
    return operations