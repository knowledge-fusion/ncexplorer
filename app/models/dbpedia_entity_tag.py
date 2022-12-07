from mongoengine import BooleanField, IntField, StringField

from app.common.mongoengine_base import BaseDocument


class DBPediaEntityTag(BaseDocument):
    meta = {"indexes": ["entity", "tag", "skip_in_analysis", "version"]}

    entity = StringField(required=True)
    tag = StringField(required=True, unique_with="entity")
    skip_in_analysis = BooleanField()
    version = IntField()

    """
    @queryset_manager
    def objects(doc_cls, queryset):
        # This may actually also be done by defining a default ordering for
        # the document, but this illustrates the use of manager methods
        return queryset.filter(skip_in_analysis__ne=True)
"""

    def __unicode__(self):
        return f"{self.entity} => {self.tag}"

    @classmethod
    def get_filter(cls, record):
        flt = {"entity": record.pop("entity"), "tag": record.pop("tag")}
        return flt
