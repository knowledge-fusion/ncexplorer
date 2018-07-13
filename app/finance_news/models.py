from mongoengine import StringField, URLField, DateTimeField, IntField, BooleanField, LongField

from app.common.mongoengine_base import BaseDocument


class Stock(BaseDocument):
    symbol = StringField(required=True)
    name = StringField()
    sector = StringField()
    industry = StringField()
    ipo_year = IntField()
    market_cap = IntField()
    craw_completed = BooleanField()
    oldest_timestamp = DateTimeField()
    latest_filing_date = DateTimeField()
    cik = StringField()  # the Central Index Key issued by the SEC, which is the unique identifier all company filings are issued under
    lei = StringField()  # lei - the Legal Entity Identifier for the company


class FinanceNews(BaseDocument):
    meta = {
        'collection': 'news',
        'indexes': [
            {'fields': ['timestamp']},
            {'fields': ['source']}
        ]
    }
    source = StringField(choices=['crawler', 'newsriver', 'intrinio'])
    symbol = StringField()
    url = URLField(required=True, unique=True)
    title = StringField()
    timestamp = IntField()
    content = StringField()
    html = StringField()
    comments_num = IntField()


class SyncStatus(BaseDocument):
    publisher = StringField(choices=['seekingalpha.com', 'ft.com', 'economic_indices',
                                     'company_news', 'stock_data'])
    provider = StringField(choices=['newsriver', 'intrinio', 'alphavantage'])
    timestamp = DateTimeField()
    last_sync_operation = DateTimeField()
    symbol = StringField()
    offset = IntField()
    has_more = BooleanField(default=True)
