from mongoengine import BooleanField, IntField, Q, StringField, queryset_manager

from app.common.mongoengine_base import BaseDocument


class DBPediaEntityLinkedAttribute(BaseDocument):
    meta = {
        "indexes": [
            "subject",
            "predicate",
            "object",
            {"fields": ["subject", "predicate", "object"], "unique": True},
            "peer_objects_count",
            "peer_subjects_count",
        ]
    }

    subject = StringField(required=True)
    predicate = StringField(required=True)
    object = StringField(required=True)
    peer_subjects_count = IntField()
    peer_objects_count = IntField()
    skip_in_analysis = BooleanField()

    def __unicode__(self):
        return f"{self.subject} => {self.predicate} {self.object}"

    @queryset_manager
    def objects(doc_cls, queryset):
        # This may actually also be done by defining a default ordering for
        # the document, but this illustrates the use of manager methods
        return queryset.filter(skip_in_analysis__ne=True)

    @classmethod
    def label_skip_in_analysis(cls):
        keywords = ".1234567890"
        for char in keywords:
            print(char)
            cls.objects(subject__startswith=char).update(set__skip_in_analysis=True)
            cls.objects(object__startswith=char).update(set__skip_in_analysis=True)

    @classmethod
    def get_filter(cls, record):
        flt = {
            "subject": record.pop("subject"),
            "predicate": record.pop("predicate"),
            "object": record.pop("object"),
        }
        return flt

    @classmethod
    def calculate_uniqueness_score(cls):
        """
        pipeline = [
            # {"$match": {"predicate": "award"}},
            {
                "$group": {
                    "_id": "$predicate",
                    "total_count": {"$sum": 1},
                },
            },
            {"$match": {"total_count": {"$gt": 10000}}},
            {
                "$project": {
                    "_id": 1,
                    "total_count": 1,
                }
            },
        ]

        start = False
        for res in cls.objects.aggregate(pipeline):
            object_count, subject_count = 0, 0
            if not start:
                print(res)
                continue
            try:
                # object_count = len(cls.objects(predicate=res["_id"]).distinct("object"))
                if True:
                    object_pipeline = [
                        {"$match": {"predicate": res["_id"]}},
                        {
                            "$group": {
                                "_id": "$object",
                                "subjects": {"$addToSet": "$subject"},
                            }
                        },
                        {
                            "$project": {
                                "_id": 1,
                                "peer_subjects_count": {"$size": "$subjects"},
                            }
                        },
                    ]

                    for item in cls.objects.aggregate(object_pipeline):
                        cls.objects(object=item["_id"], predicate=res["_id"]).update(
                            set__peer_subjects_count=item["peer_subjects_count"] - 1
                        )
            except Exception as exp:
                print(exp)

            try:
                if True:
                    object_pipeline = [
                        {"$match": {"predicate": res["_id"]}},
                        {
                            "$group": {
                                "_id": "$subject",
                                "objects": {"$addToSet": "$object"},
                            }
                        },
                        {
                            "$project": {
                                "_id": 1,
                                "peer_objects_count": {"$size": "$objects"},
                            }
                        },
                    ]

                    for item in cls.objects.aggregate(object_pipeline):
                        cls.objects(subject=item["_id"], predicate=res["_id"]).update(
                            set__peer_objects_count=item["peer_objects_count"] - 1
                        )
            except Exception as exp:
                print(exp)

            print(f"{res=}, {subject_count=} {object_count=}")

        return
        """
        if True:
            # query = Q(peer_subjects_count=None) & Q(object=entity.subject)
            #        predicates = ['careerStation']

            query = Q(predicate="birthPlace") & Q(peer_subjects_count=None)
            record = cls.objects(query).first()
            print(f"calculate_uniqueness_score {record=}")
            while record:
                # record = cls.objects(, predicate='leaderName').first()
                # how many object share the same predicate and subject
                print(record)
                pipeline = [
                    {
                        "$match": {
                            "subject": record.subject,
                            "predicate": record.predicate,
                        }
                    },
                    {
                        "$group": {
                            "_id": "$predicate",
                            "objects": {"$addToSet": "$object"},
                        }
                    },
                    {
                        "$project": {
                            "_id": 1,
                            "peer_objects_count": {"$size": "$objects"},
                        }
                    },
                ]
                # res = cls.objects.aggregate(pipeline)
                # for item in res:
                #     cls.objects(subject=record.subject, predicate=item["_id"]).update(
                #         set__peer_objects_count=item["peer_objects_count"] - 1
                #     )

                object_pipeline = [
                    {
                        "$match": {
                            "object": record.object,
                            "predicate": record.predicate,
                        }
                    },
                    {
                        "$group": {
                            "_id": "$predicate",
                            "subjects": {"$addToSet": "$subject"},
                        }
                    },
                    {
                        "$project": {
                            "_id": 1,
                            "peer_subjects_count": {"$size": "$subjects"},
                        }
                    },
                ]

                res = cls.objects.aggregate(object_pipeline)
                for item in res:
                    cls.objects(object=record.object, predicate=item["_id"]).update(
                        set__peer_subjects_count=item["peer_subjects_count"] - 1
                    )
                record = cls.objects(query).first()
