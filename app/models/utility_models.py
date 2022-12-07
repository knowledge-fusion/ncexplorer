from mongoengine import BooleanField, DateTimeField, IntField, StringField

from app.common.mongoengine_base import BaseDocument


class SyncStatus(BaseDocument):
    publisher = StringField(
        choices=[
            "seekingalpha.com",
            "ft.com",
            "economic_indices",
            "find_volatile_stock_news",
            "company_news",
            "stock_data",
            "entity_symbol",
            "market_event",
        ]
    )
    provider = StringField(choices=["newsriver", "alphavantage", "dbpedia", "tasks"])
    timestamp = DateTimeField()
    last_sync_operation = DateTimeField()
    symbol = StringField()
    offset = IntField()
    has_more = BooleanField(default=True)

    @classmethod
    def reference_field(cls):
        return cls.publisher.name

    @classmethod
    def get_filter(cls, record):
        flt = cls.default_filter(record)
        flt[cls.provider.name] = record.pop(cls.provider.name)
        return flt
