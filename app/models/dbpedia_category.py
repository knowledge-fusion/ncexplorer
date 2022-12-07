import math

from mongoengine import (
    BooleanField,
    FloatField,
    IntField,
    StringField,
    queryset_manager,
)

from app.common.mongoengine_base import BaseDocument


class DBPediaCategoryHierarchy(BaseDocument):
    meta = {
        "indexes": ["name", "parent"],
    }

    name = StringField(required=True)
    parent = StringField(required=True, unique_with="name")
    skip_in_analysis = BooleanField()

    def __unicode__(self):
        return f"{self.name} => {self.parent}"

    @classmethod
    def get_filter(cls, record):
        flt = {
            "name": record.pop("name"),
            "parent": record.pop("parent"),
        }
        return flt

    @queryset_manager
    def objects(doc_cls, queryset):
        # This may actually also be done by defining a default ordering for
        # the document, but this illustrates the use of manager methods
        return queryset.filter(skip_in_analysis__ne=True)

    @classmethod
    def label_skip_in_analysis(cls):
        keywords = ["_by_", "Template:", "_Wikipedia_", "_(band)_"]
        for keyword in keywords:
            cls.objects(name__icontains=keyword).update(set__skip_in_analysis=True)
            cls.objects(parent__icontains=keyword).update(set__skip_in_analysis=True)


class DBPediaCategory(BaseDocument):
    name = StringField(required=True, unique=True)
    vector = StringField()
    kg_entity_count = IntField()
    corpus_entity_count = IntField()
    specificity_score = FloatField()
    version = IntField()
    skip_in_analysis = BooleanField()

    @classmethod
    def get_filter(cls, record):
        flt = {
            "name": record.pop("name"),
        }
        return flt

    @queryset_manager
    def objects(doc_cls, queryset):
        # This may actually also be done by defining a default ordering for
        # the document, but this illustrates the use of manager methods
        return queryset.filter(skip_in_analysis__ne=True)

    @classmethod
    def calculate_specificity_score(cls):
        from app.models.dbpedia_entity_category import DBPediaEntityCategory

        for item in cls.objects(kg_entity_count=None):
            item.kg_entity_count = DBPediaEntityCategory.objects(
                category=item.name
            ).count()
            item.save()

        from app.models.dbpedia_entity_alias import DBPediaEntityAlias

        total_count = DBPediaEntityAlias.objects().count()
        cls.objects(kg_entity_count=0).update(set__specificity_score=0)
        item = cls.objects(kg_entity_count__ne=None, specificity_score=None).first()
        while item:
            specificity_score = 0 - math.log10(item.kg_entity_count / total_count)
            specificity_score = round(specificity_score, 3)
            cls.objects(kg_entity_count=item.kg_entity_count).update(
                set__specificity_score=specificity_score
            )
            item = cls.objects(kg_entity_count__ne=None, specificity_score=None).first()
