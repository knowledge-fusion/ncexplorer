from datetime import datetime

from mongoengine import DateTimeField, Document


# This class wraps mongoengine base Document.
# It manages document `created_at`, `updated_at` timestamp for save() and upsert_one() operations.
# It is an abstract class.
# References:
# http://stackoverflow.com/questions/3277367/how-does-pythons-super-work-with-multiple-inheritance
# http://docs.mongoengine.org/guide/defining-documents.html#document-inheritance
# http://docs.mongoengine.org/guide/querying.html#custom-querysets

# pylint: disable=unnecessary-lambda
class BaseDocument(Document):
    meta = {
        'abstract': True,
    }

    created_at = DateTimeField(required=True, default=lambda: datetime.utcnow())
    updated_at = DateTimeField(required=True, default=lambda: datetime.utcnow())

    def validate(self, clean=True):
        if not self.created_at:
            self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        return super(BaseDocument, self).validate(clean)
