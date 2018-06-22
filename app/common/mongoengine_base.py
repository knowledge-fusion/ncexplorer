
from datetime import datetime

from flask_mongoengine import BaseQuerySet
from mongoengine import DateTimeField, Document, StringField


# This class wraps mongoengine base Document.
# It manages document `created_at`, `updated_at` timestamp for save() and upsert_one() operations.
# It is an abstract class.
# References:
# http://stackoverflow.com/questions/3277367/how-does-pythons-super-work-with-multiple-inheritance
# http://docs.mongoengine.org/guide/defining-documents.html#document-inheritance
# http://docs.mongoengine.org/guide/querying.html#custom-querysets


class UpdateTimestampQuerySet(BaseQuerySet):
    def upsert_one(self, write_concern=None, **update):
        update_time = datetime.utcnow()
        update['set__updated_at'] = update_time
        result = super(UpdateTimestampQuerySet, self).upsert_one(write_concern, **update)
        if result.created_at is None:
            result.created_at = update_time
            result.save()
        return result


class BaseDocument(Document):
    meta = {
        'abstract': True,
        'queryset_class': UpdateTimestampQuerySet
    }

    created_at = DateTimeField(required=True)
    updated_at = DateTimeField(required=True)

    def validate(self, clean=True):
        if not self.created_at:
            self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        return super(BaseDocument, self).validate(clean)
