from mongoengine import (
    CASCADE,
    FloatField,
    IntField,
    ListField,
    ReferenceField,
    StringField,
)

from app.common.mongoengine_base import BaseDocument
from app.models.news_analytics import NewsAnalytics


class DocumentEntityCategory(BaseDocument):

    meta = {
        "indexes": [
            "entity",
            "category",
            "news_analytics",
            {
                "fields": ["news_analytics", "category"],
            },
            {
                "fields": ["news_analytics", "entity", "category"],
                "unique": True,
            },
            {
                "fields": ["$category"],
                "default_language": "english",
            },
        ]
    }

    news_analytics = ReferenceField(
        NewsAnalytics, required=True, reverse_delete_rule=CASCADE
    )
    entity = StringField()

    category = StringField()
    entity_count = IntField()
    expansion_routes = ListField(StringField())
    category_specificity_score = FloatField()

    concept_relevance_score = FloatField()
    calculation_time = FloatField()
    entity_relevance_score = FloatField()
    total_relevance_score = FloatField()

    version = IntField()

    def __unicode__(self):
        return f"{self.category} ({self.entity})"

    @classmethod
    def get_filter(cls, record):
        flt = {
            cls.news_analytics.name: record.pop(cls.news_analytics.name),
            cls.entity.name: record.pop(cls.entity.name),
            cls.category.name: record.pop(cls.category.name),
        }
        return flt
