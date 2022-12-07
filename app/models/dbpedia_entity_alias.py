from mongoengine import (
    BooleanField,
    DateTimeField,
    IntField,
    ListField,
    StringField,
    queryset_manager,
)

from app.common.mongoengine_base import BaseDocument


class DBPediaEntityAlias(BaseDocument):

    meta = {
        "indexes": [
            "subject",
            "alias",
            "wikidata_id",
            "derived_type",
            "historical",
            "domain",
        ]
    }

    subject = StringField(required=True, unique=True)
    derived_type = StringField()
    domain = StringField()
    dbpedia_hypernyms = StringField()
    hypernym = StringField()
    type = StringField()
    wikidata_id = StringField()
    entity_type = StringField()
    infobox_template = StringField()
    stock_ticker = ListField(StringField())
    description = StringField()
    alias = ListField(StringField())
    disambiguations = ListField(StringField())
    is_media_entity = BooleanField()
    reachability_calculated = BooleanField()
    birth_date = DateTimeField()
    death_date = DateTimeField()
    kg_node_degree = IntField()
    skip_in_analysis = BooleanField()
    historical = BooleanField()
    description = StringField()
    version = IntField()

    @property
    def link(self):
        res = f'<a href="http://dbpedia.org/resource/{self.subject}" target="_blank">link</a>'
        return res

    @property
    def hypernyms(self):
        from flask import current_app
        from networkx import shortest_path

        root = "owl#Thing"
        G = current_app.ontology_graph
        res = []
        if self.dbpedia_hypernyms:
            try:
                res = shortest_path(G, root, self.dbpedia_hypernyms)
            except Exception as e:
                print(e)
        # res = DBPediaEntityType.objects(entity=self.subject).distinct("type")
        return res

    @queryset_manager
    def objects(doc_cls, queryset):
        # This may actually also be done by defining a default ordering for
        # the document, but this illustrates the use of manager methods
        return queryset.filter(skip_in_analysis__ne=True)

    def __unicode__(self):
        return f"{self.subject}"

    @classmethod
    def get_filter(cls, record):
        flt = {
            "subject": record.pop("subject"),
        }

        return flt

    def extra_view(self):
        from app.models.dbpedia_entity_tag import DBPediaEntityTag

        tags = DBPediaEntityTag.objects(entity=self.subject).distinct("tag")
        return ",".join(tags)

    @classmethod
    def get_kg_node_degrees(cls, subjects):
        from app.news_processor.calculate_document_entity_abstraction_score import (
            _get_entity_neighbor,
        )

        current_version = 1

        results = dict()
        for subject in subjects:
            results[subject] = None
        for item in cls.objects(subject__in=subjects, version=current_version).only(
            "subject", "kg_node_degree"
        ):
            results[item.subject] = item.kg_node_degree

        missing_subjects = []
        for subject, degree in results.items():
            if not degree:
                missing_subjects.append(subject)
        updates = []
        for item in missing_subjects:
            neighbors = _get_entity_neighbor(item)
            updates.append(
                {
                    "subject": item,
                    "kg_node_degree": len(neighbors),
                    "version": current_version,
                }
            )
            results[item] = len(neighbors)
        cls.upsert_many(updates)
        return results

    @classmethod
    def label_skip_in_analysis(cls):
        templates = ["Country_At_Games", "Ship_Characteristics"]
        cls.objects(infobox_template__in=templates).update(set__skip_in_analysis=True)

    @classmethod
    def print_hypernym_count(cls):
        from app.common.models import SystemConfig

        all_mappings = SystemConfig.get_or_create_dict_value(
            key="infobox_template_mapping"
        )

        record = cls.objects(
            derived_type=None, hypernym__ne=None, infobox_template__ne=None
        ).first()
        # queryset = cls.objects(infobox_template='Logical_Connective')
        while record:
            queryset = cls.objects(infobox_template=record.infobox_template)
            derived_type = record.infobox_template
            if queryset.count() < 1000:

                template_type_pipeline = [
                    {
                        "$match": {
                            "infobox_template": record.infobox_template,
                            # "derived_type": {"$exists": False},
                        }
                    },
                    {
                        "$group": {
                            "_id": "$hypernym",
                            "total_count": {"$sum": 1},
                        },
                    },
                    {
                        "$project": {
                            "_id": 1,
                            "total_count": 1,
                        }
                    },
                    {
                        "$sort": {
                            "total_count": 1,
                        }
                    },
                ]
                derived_type = None
                for item in cls.objects.aggregate(template_type_pipeline):
                    print(
                        f"{record.infobox_template} => {item['_id']} ({item['total_count']})"
                    )
                    if item["_id"]:
                        derived_type = item["_id"]
            print(
                f"{record.infobox_template=}, {derived_type=} count={queryset.count()}"
            )
            DBPediaEntityAlias.objects(infobox_template=record.infobox_template).update(
                set__derived_type=derived_type
            )
            all_mappings[record.infobox_template] = derived_type
            record = cls.objects(
                derived_type=None, hypernym__ne=None, infobox_template__ne=None
            ).first()
            SystemConfig.update_dict_value(
                key="infobox_template_mapping", val=all_mappings
            )
        print(all_mappings)
