from mongoengine import CASCADE, FloatField, IntField, ReferenceField, StringField

from app.common.mongoengine_base import BaseDocument
from app.models.news_analytics import NewsAnalytics


class DocumentEntity(BaseDocument):
    news_analytics = ReferenceField(
        NewsAnalytics, required=True, reverse_delete_rule=CASCADE
    )
    entity = StringField()
    entity_type = StringField()
    entity_tfidf_score = FloatField()
    version = IntField()

    meta = {
        "indexes": [
            "entity",
            "news_analytics",
            {
                "fields": ["news_analytics", "entity"],
                "unique": True,
            },
        ]
    }

    def __unicode__(self):
        return f"{self.entity}"

    @classmethod
    def get_filter(cls, record):
        flt = {
            cls.news_analytics.name: record.pop(cls.news_analytics.name),
            cls.entity.name: record.pop(cls.entity.name),
        }
        return flt
