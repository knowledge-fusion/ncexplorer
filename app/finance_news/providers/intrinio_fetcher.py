import calendar
import os
from datetime import datetime

import intrinio
from dateutil import parser
from pymongo import UpdateOne

from app.finance_news.models import Stock, SyncStatus, FinanceNews
from app.timeseries.models import EconomicIndex
from app.utils import graceful_auto_reconnect


# pylint: disable=no-self-use
@graceful_auto_reconnect
def get_sync_status(symbol):
    publisher = 'company_news'
    status = SyncStatus.objects(publisher=publisher, symbol=symbol,
                                provider='intrinio').first()
    return status


class IntrinioFetcher(object):
    name = 'intrinio'

    def __init__(self, username=None, password=None):
        basepath = os.path.dirname(__file__)
        relativepath = '../../../tests/finance_news/data/intrinio'
        filepath = os.path.abspath(os.path.join(basepath, relativepath))
        intrinio.client.cache_directory = filepath
        if username:
            intrinio.client.username = username
            intrinio.client.password = password
        self.intrinio = intrinio

    def fetch_companies(self):
        df = intrinio.get('companies')
        operations = []
        for row in df.to_dict('records'):
            row['symbol'] = row.pop('ticker')
            if row.get('latest_filing_date', None):
                row['latest_filing_date'] = parser.parse(row['latest_filing_date'])
            operations.append(UpdateOne({'symbol': row['symbol']}, {'$set': row},
                                        upsert=True))
        Stock._get_collection().bulk_write(operations, ordered=False)

    def fetch_economic_indices(self):
        status = SyncStatus.objects(publisher='economic_indices', provider=self.name).first()
        if not status:
            status = SyncStatus(
                publisher='economic_indices',
                provider=self.name,
                offset=1
            )

        while True:
            page = intrinio.get_page('indices', page_number=status.offset, type='economic')

            if not page or status.offset == page.total_pages:
                status.has_more = False
                status.save()
                break

            operations = []
            for row in page.to_dict('records'):
                for key in ['observation_start', 'last_updated', 'observation_end']:
                    if row.get(key, None):
                        row[key] = parser.parse(row[key])
                operations.append(UpdateOne(
                    {
                        'index_name': row['index_name'],
                        'observation_start': row['observation_start'],
                        'observation_end': row['observation_end']
                    },
                    {'$set': row},
                    upsert=True))
            EconomicIndex._get_collection().bulk_write(operations, ordered=False)

            status.offset += 1
            status.last_sync_operation = datetime.utcnow()
            status.save()

    def fetch_company_news(self, symbol):
        status = get_sync_status(symbol)

        while True:
            page = intrinio.get_page('news', page_number=status.offset, identifier=symbol)
            if not page or status.offset == page.total_pages:
                status.has_more = False
                status.save()
                break
            operations = []
            for row in page.to_dict('records'):
                timestamp = calendar.timegm(
                    parser.parse(row.pop('publication_date')).timetuple())
                row['timestamp'] = timestamp
                row['content'] = row.pop('summary')
                row['source'] = self.name
                operations.append(UpdateOne(
                    {'url': row['url']},
                    {'$set': row},
                    upsert=True))
            FinanceNews._get_collection().bulk_write(operations, ordered=False)
            status.offset += 1
            status.last_sync_operation = datetime.utcnow()
            status.save()
