from mongoengine import (
    PULL,
    BooleanField,
    FloatField,
    IntField,
    ListField,
    ReferenceField,
    StringField,
)

from app.common.mongoengine_base import BaseDocument
from app.models.news_analytics import NewsAnalytics


class AbstractionCooccurrenceCount(BaseDocument):
    meta = {
        "indexes": [
            {"fields": ["abstraction_pair"], "unique": True},
            "-count",
            "abstract1",
            "abstract2",
            "documents",
            "least_common_subsumer_depth",
            {"fields": ["simple_paths", "simple_paths_too_large", "updated_at"]},
        ]
    }

    @classmethod
    def get_filter(cls, record):
        flt = {}
        flt[cls.abstraction_pair.name] = record.pop(cls.abstraction_pair.name)
        return flt

    abstract1 = StringField(required=True)
    abstract2 = StringField(unique_with="abstract1", required=True)
    abstraction_pair = StringField(required=True)
    count = IntField()
    documents = ListField(ReferenceField(NewsAnalytics, reverse_delete_rule=PULL))
    simple_paths = ListField(ListField(StringField()))
    simple_paths_too_large = BooleanField()
    semantic_connectivity_score = FloatField()
    least_common_subsumer = StringField()
    least_common_subsumer_depth = IntField()

    def __str__(self):
        return f"{self.abstraction_pair} {self.count}"
