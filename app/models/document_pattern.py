from enum import Enum

from mongoengine import (
    PULL,
    BooleanField,
    DictField,
    FloatField,
    IntField,
    ListField,
    ReferenceField,
    StringField,
)

from app.common.mongoengine_base import BaseDocument
from app.models.news_analytics import NewsAnalytics
from app.utils import get_enum_values


class DocumentPatternProcessingState(Enum):
    DOCUMENTS_OUTDATED = "documents_outdated"
    DOCUMENTS_UPDATED = "documents_updated"
    SCORE_UPDATED = "score_updated"
    EXPANDED = "expanded"


class DocumentPattern(BaseDocument):
    meta = {
        "indexes": [
            "document_count",
            "diversity_score",
            "categories",
            "documents",
            "trending",
            "processing_state",
            "category_count",
            "relevance_score",
            {
                "fields": ["$name"],
                "default_language": "english",
            },
            {
                "fields": ["document_count", "category_count"],
            },
        ]
    }

    name = StringField(required=True, unique=True)

    categories = ListField(StringField())

    relevance_score = FloatField()

    diversity_score = FloatField()

    diversity_scores = DictField()
    version = IntField()
    document_count = IntField()
    documents = ListField(ReferenceField(NewsAnalytics, reverse_delete_rule=PULL))
    document_bert_score = DictField()

    category_count = IntField()
    abstract_search_result = DictField()

    bm25_cosine_similarity_result = DictField()
    bert_cosine_similarity_result = DictField()

    bm25_result_count = IntField()
    bm25_average_score = FloatField()
    bert_average_score = FloatField()

    trending = BooleanField()

    news_link_entities = ListField(StringField())
    news_link_result = DictField()

    processing_state = StringField(
        choices=get_enum_values(DocumentPatternProcessingState)
    )

    @classmethod
    def get_filter(cls, record):
        flt = {"name": record["name"]}

        return flt

    def __unicode__(self):
        return f"{self.name}"

    @classmethod
    def update_document_count(cls):
        pipeline = [
            {"$match": {"processing_state": {"$exists": True}}},
            {
                "$project": {
                    "name": 1,
                    "document_count": {
                        "$cond": {
                            "if": {"$isArray": "$documents"},
                            "then": {"$size": "$documents"},
                            "else": 0,
                        }
                    },
                    "category_count": {"$size": "$categories"},
                }
            },
        ]
        res = cls.objects.aggregate(pipeline)

        results = list(res)
        res = cls.upsert_many(results)
        return results
