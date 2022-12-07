import hashlib
import itertools
import json
from collections import defaultdict
from enum import Enum

from mongoengine import (
    BooleanField,
    DateTimeField,
    DictField,
    FloatField,
    IntField,
    StringField,
)

from app.common.mongoengine_base import BaseDocument
from app.news_search.search_by_abstraction import get_news_by_abstractions_v2
from app.news_search.search_by_entity import get_news_by_entities
from app.utils import get_enum_values


class NewsAnalyticsProcessingState(Enum):
    NAMED_ENTITY_LINKED = "Named Entity Linked"
    DOCUMENT_ABSTRACTION_EXTRACTED = "Document Abstraction Extracted"
    DOCUMENT_ENTITY_SCORE_CALCULATED = "Document Entity Score Calculated"
    DOCUMENT_ENTITY_ABSTRACTION_SCORE_CALCULATED = (
        "Document Entity Abstraction Score Calculated"
    )
    DOCUMENT_ENTITY_ABSTRACTION_EXPANSION_SCORE_CALCULATED = (
        "Document Entity Abstraction Expansion Score Calculated"
    )
    ENTITY_COOCCURENCE_UPDATED = "Entity Cooccurence Updated"
    ABSTRACTION_COOCCURENCE_UPDATED = "Abstraction Cooccurence Updated"
    DOCUMENT_SEED_PATTERN_REGISTERED = "Document Seed Pattern Registered"
    DOCUMENT_PATTERN_SCORE_CALCULATED = "Document Pattern Score Calculated"
    GLOBAL_BEST_ABSTRACTION = "Calculate Global Abstraction Calculated"
    LOCAL_BEST_ABSTRACTION = "Calculate Local Abstraction Calculated"
    SENTIMENT_SCORE_CALCULATED = "Sentiment Score Calculated"


class NewsAnalytics(BaseDocument):
    meta = {
        "indexes": [
            {"fields": ["title"]},
            {
                "fields": ["url"],
            },
            {
                "fields": ["source"],
            },
            {
                "fields": ["url", "source"],
            },
            {
                "fields": ["$text"],
                "default_language": "english",
            },
            "version",
            "processing_state",
            "publication_date",
        ]
    }
    url = StringField(required=True, unique=True)
    publication_date = DateTimeField(required=True)
    title = StringField(required=True, unique=True)
    spacy_json = DictField()
    text = StringField(required=True)
    hash_digest = StringField(required=True, unique=True)
    version = IntField()
    entity_html = StringField()
    source = StringField()
    processing_state = StringField(
        choices=get_enum_values(NewsAnalyticsProcessingState)
    )

    connect_component_analyzed = BooleanField()
    vector = StringField()
    sentiment_score = FloatField()
    # cache

    def get_entity_stats(self):
        from app.models.dbpedia_entity_alias import DBPediaEntityAlias
        from app.models.document_entity import DocumentEntity

        queryset = DocumentEntity.objects(news_analytics=self.id).order_by(
            "-entity_tfidf_score"
        )

        res = dict()

        for item in queryset:
            res[item.entity] = json.loads(item.to_json())

        for item in DBPediaEntityAlias.objects(subject__in=list(res.keys())):
            item = json.loads(item.to_json())
            item["kg_entity_type"] = item.pop("derived_type", "")
            res[item["subject"]].update(item)
        return res

    @property
    def entity_abstractions(self):
        from app.models.dbpedia_category import DBPediaCategory
        from app.models.document_entity_category import DocumentEntityCategory

        queryset = DocumentEntityCategory.objects(news_analytics=self.id).order_by(
            "-total_relevance_score"
        )
        result = defaultdict(list)
        category_ids = []
        for item in queryset:
            result[item.entity].append(item)
            if item.category.find("Category:") > -1:
                category_ids.append(item.category)

        category_queryset = DBPediaCategory.objects(name__in=category_ids)
        for entity, concepts in result.items():
            for concept in concepts:
                category = category_queryset.filter(name=concept.category).first()
                if category:
                    concept.category_specificity_score = category.specificity_score
                    concept.kg_entity_count = category.kg_entity_count

        return result

    @property
    def recognized_entities(self):
        from app.models.document_entity import DocumentEntity

        return DocumentEntity.objects(news_analytics=self.id).distinct("entity")

    def similar_news_by_entity(self):
        from app.models.document_entity_category import DocumentEntityCategory

        dbpedia_ids = DocumentEntityCategory.objects(news_analytics=self.id).distinct(
            "entity"
        )
        results = get_news_by_entities(
            dbpedia_ids=dbpedia_ids, news_ids_to_exclude=[self.id], limit=100
        )
        results.sort(key=lambda x: len(x["entities"]), reverse=True)
        return results

    def similar_news_by_abstraction(self):
        # es = get_news_by_abstractions(self.url, news_ids_to_exclude=[self.id])
        res = {}, []
        return res

    def similar_news_by_abstraction_v2(self):
        res = get_news_by_abstractions_v2(
            self.url,
            news_ids_to_exclude=[self.id],
        )
        return res

    def all_abstraction_pairs(self):
        from app.models.document_entity_category import DocumentEntityCategory

        queryset = DocumentEntityCategory.objects(news_analytics=self.id)
        dbpedia_ids = {item.entity for item in queryset}
        dbpedia_id_pairs = itertools.combinations(dbpedia_ids, 2)
        abstraction_entity_map = dict()
        entity_ontology_map = dict()
        for item in queryset:
            entity_ontology_map[item.entity] = entity_ontology_map.get(item.entity, [])
            entity_ontology_map[item.entity].append(item.category)
            abstraction_entity_map[item.category] = item.entity

        category_set = set()
        for dbpedia_id_pair in dbpedia_id_pairs:
            abstraction_pairs = itertools.product(
                entity_ontology_map[dbpedia_id_pair[0]],
                entity_ontology_map[dbpedia_id_pair[1]],
            )
            abstraction_pairs = {
                item for item in abstraction_pairs if item[0] != item[1]
            }
            category_set = category_set.union(abstraction_pairs)
        abstraction_key_ontology_map = dict()
        DELIMITER = "|||"

        for ontology1, ontology2 in category_set:
            abstraction_set = [ontology1, ontology2]
            abstraction_set.sort()
            key = DELIMITER.join([item for item in abstraction_set])
            abstraction_key_ontology_map[key] = [ontology1, ontology2]
        return abstraction_entity_map, abstraction_key_ontology_map

    @classmethod
    def reference_field(cls):
        return cls.url.name

    def validate(self, clean=True):
        if not self.hash_digest:
            digest = hashlib.sha3_512(self.text.encode("utf-8")).hexdigest()
            self.hash_digest = digest
        super().validate(clean)

    def __unicode__(self):
        summary = self.title if self.title else self.text[0:15]
        summary += f"<a href='/admin/newsanalytics/details/?id={self.id}'  target='_blank'> View</a>"
        return summary

    def extra_view(self):
        doc = self.spacy_json

    def render_spacy_entity_html(self, entity_abstraction_map, add_explaination=False):
        from spacy import displacy

        entities = []
        for entity, abstraction in entity_abstraction_map.items():
            if entity.find("dbpedia") == -1:
                entity = f"http://dbpedia.org/resource/{entity}"
            entities.append(entity)

        json_doc = self.spacy_json
        ents = [
            item
            for item in json_doc["ents"]
            if item["params"]["dbpedia_id"] in entities
            and item["params"]["dbpedia_label"]
        ]

        json_doc["ents"] = ents

        TPL_ENT = """
            <mark class="entity" style="background: {bg}; padding: 0.45em 0.6em; margin: 0
            0.25em; line-height: 1; border-radius: 0.35em;">
                {text}
                <span style="font-size: 0.8em; font-weight: bold; line-height: 1; border-radius:
                0.35em; text-transform: uppercase; vertical-align: middle; margin-left: 0.5rem">
                <a href="{dbpedia_id}" target="_black">{dbpedia_label}</a>
                </span>
            </mark>
            """
        options = {
            "ents": [
                "PERSON",
                "ORG",
                "PRODUCT",
                "NORP",
                "GPE",
                "UNKNOWN",
                "LOC",
                "EVENT",
                "DISEASE",
                "DRUG",
                "ACTION",
            ],
            "template": TPL_ENT,
        }

        html = displacy.render(
            json_doc,
            style="ent",
            options=options,
            manual=True,
            jupyter=False,
            minify=True,
        )
        if add_explaination:
            explainations = []
            for entity, abstraction in entity_abstraction_map.items():
                explainations.append(
                    f"<b>{entity.replace('_', ' ')}</b>: {abstraction}"
                )
            html += ", ".join(explainations)
        return html
