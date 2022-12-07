from datetime import datetime

from bson import ObjectId
from flask import current_app
from mongoengine import DateTimeField, Document, MultipleObjectsReturned, Q

# pylint: disable=unnecessary-lambda
from pymongo import ReadPreference, UpdateOne
from pymongo.errors import BulkWriteError

# This class wraps mongoengine base Document.
# It manages document `created_at`, `updated_at` timestamp for save() and upsert_one() operations.
# It is an abstract class.
# References:
# http://stackoverflow.com/questions/3277367/how-does-pythons-super-work-with-multiple-inheritance
# http://docs.mongoengine.org/guide/defining-documents.html#document-inheritance
# http://docs.mongoengine.org/guide/querying.html#custom-querysets


class BaseDocument(Document):
    meta = {"abstract": True, "indexes": [{"fields": ["updated_at"]}]}

    created_at = DateTimeField(required=True)
    updated_at = DateTimeField(required=True)

    def validate(self, clean=True):
        if not self.created_at:
            self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        return super().validate(clean)

    @classmethod
    def default_filter(cls, record):
        key = cls.reference_field()
        field = record.pop(key)
        if not isinstance(field, (str, ObjectId)):
            field = field.id
        flt = {key: field}
        return flt

    @classmethod
    def get_filter(cls, record):
        flt = cls.default_filter(record)
        return flt

    @classmethod
    def upsert(cls, record=None):
        now = datetime.utcnow()
        record["updated_at"] = now

        flt = cls.get_filter(record)
        update = {}
        for key in record.keys():
            update["set__%s" % key] = record[key]
        try:
            result = cls.objects(**flt).upsert_one(**update)
            if result.created_at is None:
                result.created_at = now
                result.save()
        except MultipleObjectsReturned as e:
            current_app.logger.error(e)
            cls.objects(**flt).delete()
            result = cls.objects(**flt).upsert_one(**update)
        return result

    @classmethod
    def upsert_many(cls, records):
        from pymongo import UpdateOne

        now = datetime.utcnow()
        bulk_operations = []
        filters = []
        for record in records:
            flt = cls.get_filter(record)

            filters.append(flt)
            if not record:
                bulk_operations.append(
                    UpdateOne(
                        flt,
                        {"$setOnInsert": {"created_at": now, "updated_at": now}},
                        upsert=True,
                    )
                )
            else:
                bulk_operations.append(
                    UpdateOne(
                        flt,
                        {
                            "$set": record,
                            "$setOnInsert": {"created_at": now, "updated_at": now},
                        },
                        upsert=True,
                    )
                )
        res = {"errors": []}

        if not bulk_operations:
            return res
        try:
            result = cls._get_collection().bulk_write(bulk_operations, ordered=False)
            res.update(result.bulk_api_result)
            if result.modified_count > 0:
                queries = None
                for flt in filters:
                    if queries:
                        queries |= Q(**flt)
                    else:
                        queries = Q(**flt)

                modified_count = (
                    cls.objects(queries)
                    .read_preference(ReadPreference.PRIMARY)
                    .update(set__updated_at=now)
                )
                if modified_count == 0:
                    current_app.logger.error(
                        "modified_count",
                        extra={
                            "queries": "%s" % queries,
                            "filters": "%s" % filters,
                            "result": result,
                            "bulk_operations": bulk_operations,
                        },
                    )
        except BulkWriteError as e:
            from sentry_sdk import configure_scope

            with configure_scope() as scope:
                scope.set_extra("details", e.details)
                scope.set_extra(
                    "error", e.details.get("writeErrors")[0].get("op", {}).get("q")
                )
                current_app.logger.error(e, exc_info=True)
            res["errors"].append(e.details)
        return res

    @classmethod
    def update_many(cls, records):
        now = datetime.utcnow()
        bulk_operations = []
        for record in records:
            flt = {}
            if record.get("_id"):
                flt = {"_id": record.pop("_id")}
            record["updated_at"] = now
            bulk_operations.append(
                UpdateOne(
                    flt,
                    {
                        "$set": record,
                        "$setOnInsert": {"created_at": now, "updated_at": now},
                    },
                    upsert=True,
                )
            )
        res = {"errors": []}
        try:
            if bulk_operations:
                res = cls._get_collection().bulk_write(bulk_operations, ordered=False)
        except BulkWriteError as e:
            current_app.logger.error(e, extra={"details": e.details})
            res = e.details
        return res
