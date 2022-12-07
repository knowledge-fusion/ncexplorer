from mongoengine import StringField

from app.common.mongoengine_base import BaseDocument


class DocumentPatternSubscription(BaseDocument):
    meta = {"indexes": ["name", "email"]}

    name = StringField(required=True)
    email = StringField(required=True, unique_with="name")

    @classmethod
    def get_filter(cls, record):
        flt = {"name": record["name"], "email": record["email"]}
        return flt

    def __unicode__(self):
        return f"{self.name}"
