from mongoengine import BooleanField, StringField

from app.common.mongoengine_base import BaseDocument


class DBPediaEntityWikilink(BaseDocument):
    meta = {
        "indexes": [
            "subject",
            "object",
            {"fields": ["subject", "object"], "unique": True},
        ]
    }

    subject = StringField(required=True)
    object = StringField(required=True)
    is_media_entity = BooleanField()

    def __unicode__(self):
        return f"{self.subject} => {self.object}"

    @classmethod
    def get_filter(cls, record):
        flt = {
            "subject": record.pop("subject"),
            "object": record.pop("object"),
        }
        return flt
