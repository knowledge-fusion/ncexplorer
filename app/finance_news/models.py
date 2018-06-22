from mongoengine import StringField, URLField, DateTimeField, IntField

from app.common.mongoengine_base import BaseDocument


class FinanceNews(BaseDocument):
    meta = {
        'collection': 'news'
    }
    symbol = StringField()
    url = URLField(required=True)
    title = StringField()
    timestamp = DateTimeField()
    content = StringField()
    html = StringField()
    comments_num = IntField()
