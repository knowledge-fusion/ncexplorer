from mongoengine import StringField, URLField, DateTimeField, IntField, BooleanField, LongField

from app.common.mongoengine_base import BaseDocument


class Stock(BaseDocument):
    symbol = StringField(required=True)
    name = StringField()
    sector = StringField()
    craw_completed = BooleanField()
    oldest_timestamp = DateTimeField()


class FinanceNews(BaseDocument):
    meta = {
        'collection': 'news',
        'indexes': [
            {'fields': ['timestamp']},
            {'fields': ['source']}
        ]
    }
    source = StringField(choices=['crawler', 'newsriver'])
    symbol = StringField()
    url = URLField(required=True, unique=True)
    title = StringField()
    timestamp = IntField()
    content = StringField()
    html = StringField()
    comments_num = IntField()


class SyncStatus(BaseDocument):
    publisher = StringField(choices=['seekingalpha.com', 'ft.com'])
    provider = StringField(choices=['newsriver'])
    timestamp = DateTimeField()
    last_sync_operation = DateTimeField()
