from mongoengine import (
    BooleanField,
    DateTimeField,
    FloatField,
    IntField,
    ListField,
    LongField,
    ReferenceField,
    StringField,
)

from app.common.mongoengine_base import BaseDocument

# pylint: disable=line-too-long
from app.models.news import News


class StockData(BaseDocument):
    meta = {
        "abstract": True,
    }
    symbol = StringField(required=True)
    open = FloatField(required=True)
    high = FloatField(required=True)
    low = FloatField(required=True)
    close = FloatField(required=True)
    volume = LongField(required=True)
    delta = FloatField()


class StockDailyTimeSeries(StockData):
    meta = {
        "indexes": [
            {"fields": ["symbol"]},
            {"fields": ["date"]},
            {"fields": ["symbol", "date"]},
            {"fields": ["previous_week_entities"], "sparse": True},
            {"fields": ["same_day_entities"], "sparse": True},
            {"fields": ["following_week_entities"], "sparse": True},
            {
                "fields": ["total_entities"],
            },
            {
                "fields": ["delta"],
            },
        ]
    }
    date = DateTimeField(required=True, unique_with="symbol")
    adjusted_close = FloatField()
    dividend_amount = FloatField()
    split_coefficient = FloatField()

    previous_week_news = ListField(ReferenceField(News), default=[])
    same_day_news = ListField(ReferenceField(News), default=[])
    following_week_news = ListField(ReferenceField(News), default=[])

    previous_week_entities = ListField(StringField())
    same_day_entities = ListField(StringField())
    following_week_entities = ListField(StringField())

    previous_week_news_title = ListField(StringField())
    same_day_news_title = ListField(StringField())
    following_week_news_title = ListField(StringField())

    previous_week_concepts = ListField(StringField())
    same_day_concepts = ListField(StringField())
    following_week_concepts = ListField(StringField())

    previous_week_categories = ListField(StringField())
    same_day_categories = ListField(StringField())
    following_week_categories = ListField(StringField())

    total_entities = IntField()


class EconomicIndex(BaseDocument):
    """
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
    }
    """

    meta = {
        "indexes": [
            {
                "fields": ["index_name", "observation_start", "observation_end"],
                "unique": True,
            },
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
    cik = StringField()  # the Central Index Key issued by the SEC
    lei = StringField()  # lei - the Legal Entity Identifier for the company
    craw_started = DateTimeField()

    @classmethod
    def reference_field(cls):
        return cls.symbol.name

    def __str__(self):
        return f"{self.symbol} ({self.name})"
