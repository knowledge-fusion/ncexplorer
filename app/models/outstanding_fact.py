from mongoengine import FloatField, IntField, Q, StringField

from app.common.mongoengine_base import BaseDocument


class OutstandingFact(BaseDocument):
    meta = {
        "indexes": ["fact_id", "fact", "target_entity_id", "target_entity"],
    }

    name = StringField()
    category = StringField()
    target_entity_id = StringField()
    target_entity = StringField()
    attribute = StringField()
    fact_id = StringField()
    fact = StringField()
    target_fact_count = IntField()
    e_score = FloatField()
    num_peer_has_attribute = IntField()
    peer_size = IntField()
    fact_space_size = IntField()
    filename = StringField()

    @classmethod
    def get_filter(cls, record):
        flt = {
            "name": record.pop("name"),
            "category": record.pop("category"),
            "target_entity_id": record.pop("target_entity_id"),
            "attribute": record.pop("attribute"),
            "fact_id": record.pop("fact_id"),
        }

        return flt

    @classmethod
    def fill_entity(cls):
        from app.common.models import SystemConfig
        from app.models.dbpedia_entity_alias import DBPediaEntityAlias

        key = "missing_wikidata_id"
        config = SystemConfig.objects(key=key).first()
        if not config:
            config = SystemConfig(key=key, value="")
        missing_ids = config.value.split(",")
        queryset = cls.objects(
            # (Q(target_entity=None) & Q(target_entity_id__nin=missing_ids)) |
            Q(fact=None)
            & Q(fact_id__nin=missing_ids)
        ).limit(1000)
        while queryset:
            for item in queryset:
                entity_wikiid_result = DBPediaEntityAlias.objects(
                    wikidata_id__in=[item.target_entity_id, item.fact_id]
                )

                if not entity_wikiid_result:
                    missing_ids.append(item.target_entity_id)
                    missing_ids.append(item.fact_id)

                for entity_alias in entity_wikiid_result:
                    if entity_alias.wikidata_id:
                        res1 = cls.objects(Q(fact_id=entity_alias.wikidata_id)).update(
                            set__fact=entity_alias.subject
                        )
                        res2 = cls.objects(
                            Q(target_entity_id=entity_alias.wikidata_id)
                        ).update(set__target_entity=entity_alias.subject)

                        res1
            config.value = ",".join(missing_ids)
            config.save()
            queryset = cls.objects(
                target_entity=None,
                # fact=None,
                # fact_id__nin=missing_ids,
                target_entity_id__nin=missing_ids,
            ).limit(1000)

    @classmethod
    def import_facts(cls):
        import csv
        import pathlib

        filename = "factsCXT.csv"
        filepath = pathlib.Path(__file__).parent.absolute()

        csvfile = str(filepath) + "/../evaluation/outstanding_facts/" + filename
        print(csvfile)
        # opening the CSV file
        with open(csvfile) as file:
            # reading the CSV file
            csvFile = csv.reader(file)
            next(csvFile)
            records = []
            idx = 0
            for line in csvFile:
                idx += 1
                record = {
                    "name": line[0],
                    "category": line[1],
                    "target_entity_id": line[2],
                    "attribute": line[3],
                    "fact_id": line[4],
                    "target_fact_count": line[5],
                    "e_score": float(line[6]),
                    "num_peer_has_attribute": int(line[7]),
                    "peer_size": int(line[8]),
                    "fact_space_size": int(line[9]),
                    "filename": filename,
                }
                records.append(record)

                if len(records) % 1000 == 0:
                    update_result = cls.upsert_many(records)
                    records = []
            if records:
                cls.upsert_many(records)

    @classmethod
    def delete_none_outstanding_facts(cls):
        relationships = [
            "r-advertises",
            "r-copyright holder",
            "r-operator",
            "product or material produced",
            "r-merged into",
            "r-subsidiary",
            "owned by",
            "r-publisher",
            "r-record label",
            "r-developer",
            "r-manufacturer",
            "subsidiary",
            "permanent duplicated item",
            "r-occupant",
            "owner of",
            "r-owned by",
            "r-distributed by",
            "r-founded by",
            "r-parent organization",
            "r-replaced by",
            "r-employer",
            "named after",
            "r-issued by",
            "r-part of",
            "r-designed by",
            "r-named after",
            "r-creator",
            "r-author",
            "business division",
            "motto",
            "r-organizer",
            "copyright license",
            "stock exchange",
        ]
        cls.objects(attribute__in=relationships).delete()
