from flask_mongoengine.wtf.fields import DictField
from mongoengine import IntField, ReferenceField

from app.common.mongoengine_base import BaseDocument
from app.models.news_analytics import NewsAnalytics


class NewsSearchResult(BaseDocument):
    news_analytics = ReferenceField(NewsAnalytics, required=True)
    similar_news_by_entity = DictField()
    similar_news_by_abstraction = DictField()
    similar_news_by_entity_count = IntField()
    similar_news_by_abstraction_count = IntField()

    @classmethod
    def get_filter(cls, record):
        flt = {}
        flt[cls.news_analytics.name] = record.pop(cls.news_analytics.name)
        return flt
