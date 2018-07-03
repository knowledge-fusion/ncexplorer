from mongoengine import FloatField, StringField, DateTimeField, LongField

from app.common.mongoengine_base import BaseDocument


class StockData(BaseDocument):
    meta = {
        'abstract': True,
    }
    symbol = StringField(required=True)
    open = FloatField(required=True)
    high = FloatField(required=True)
    low = FloatField(required=True)
    close = FloatField(required=True)
    volume = LongField(required=True)


class StockDailyTimeSeries(StockData):
    date = DateTimeField(required=True, unique_with='symbol')
    adjusted_close = FloatField()
    dividend_amount = FloatField()
    split_coefficient = FloatField()
