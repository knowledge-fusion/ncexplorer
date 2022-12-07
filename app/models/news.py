from enum import Enum

from mongoengine import DateTimeField, DictField, IntField, StringField

from app.common.mongoengine_base import BaseDocument
from app.utils import get_enum_values


class NewsProcessingState(Enum):
    EMPTY = "empty"
    IMPORTED = "imported"
    CLEANED = "cleaned"
    ANALYZED = "analyzed"
    SKIPPED = "skipped"
    ANALYZE_ERROR = "analyze_error"


class News(BaseDocument):
    meta = {
        "indexes": [
            {"fields": ["source", "processing_state"]},
            "processing_state",
            "title",
            "url",
            "datetime",
            "source",
        ]
    }
    source = StringField(
        choices=[
            "seekingalpha",
            "newsriver",
            "reuters",
            "nyt",
            "aggregator",
            "ft",
            "bloomberg",
            "ap",
            "caixin",
        ]
    )
    url = StringField(required=True, unique=True)
    title = StringField(required=True, unique=True)
    snippet = StringField()
    datetime = DateTimeField()
    content = StringField()
    html = StringField()
    comments_num = IntField()
    processing_state = StringField(choices=get_enum_values(NewsProcessingState))
    extra_data = DictField()

    @classmethod
    def reference_field(cls):
        return cls.url.name
