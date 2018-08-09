from mongoengine import FloatField, StringField, DateTimeField, LongField, IntField

from app.common.mongoengine_base import BaseDocument

# pylint: disable=line-too-long
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
    meta = {
        'indexes': [
            {'fields': ['symbol']},
        ]
    }
    date = DateTimeField(required=True, unique_with='symbol')
    adjusted_close = FloatField()
    dividend_amount = FloatField()
    split_coefficient = FloatField()


class EconomicIndex(BaseDocument):
    '''
    {
   "symbol":"$BUS54TAXABL144QNSA",
   "index_name":"Revenues from Business for Professional, Scientific, and Technical Services, Establishments Subject to Federal Income Tax",
   "fred_symbol":"BUS54TAXABL144QNSA",
   "update_frequency":"quarterly",
   "last_updated":"2015-12-10T19:46:07.000+00:00",
   "description":"For further information regarding Quarterly Services, visit the source website at http://www.census.gov/services/",
   "observation_start":"2006-07-01",
   "observation_end":"2015-07-01",
   "popularity":0,
   "seasonal_adjustment":"Not Seasonally Adjusted",
   "seasonal_adjustment_short":"NSA",
   "units":"Millions of Dollars",
   "units_short":"Mil. of $",
   "index_type":"economic"
    '''
    meta = {
        'indexes': [
            {'fields': ['index_name', 'observation_start', 'observation_end'], 'unique': True},
        ]
    }
    symbol = StringField()
    index_name = StringField()
    fred_symbol = StringField()
    update_frequency = StringField()
    last_updated = DateTimeField()
    description = StringField()
    observation_start = DateTimeField()
    observation_end = DateTimeField()
    popularity = IntField()
    seasonal_adjustment = StringField()
    seasonal_adjustment_short = StringField()
    units = StringField()
    units_short = StringField()
    index_type = StringField()
