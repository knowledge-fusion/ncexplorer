from flask import current_app
from mongoengine import Q

from app.common.settings import ignored_entity_type
from app.models.news_analytics import NewsAnalytics, NewsAnalyticsProcessingState

# create entry in DocumentAbstraction
from app.utils import is_valid_abstraction


def _extract_document_entity_abstraction(url_or_news_analytics):
    from app.common.settings import ENGLISH_STOP_WORDS, pronouns
    from app.models.document_entity import DocumentEntity
    from app.models.document_entity_category import DocumentEntityCategory
    from app.models.news_analytics import NewsAnalytics

    analytics = url_or_news_analytics
    if not hasattr(url_or_news_analytics, "id"):
        analytics = NewsAnalytics.objects(url=url_or_news_analytics).first()

    non_verb_dbpedia_ids = set()
    verb_dbpedia_ids = set()
    prefix = current_app.config["DBPEDIA_PREFIX"]
    for ent in analytics.spacy_json.get("ents", []):
        if ent["params"].get("dbpedia_id"):
            id = ent["params"].get("dbpedia_id").split(prefix)[-1].replace(" ", "_")
            if id.lower() in ENGLISH_STOP_WORDS or pronouns.find(id.lower()) > -1:
                print(f"ignore entity {non_verb_dbpedia_ids}")
                continue
            if ent["label"] in ignored_entity_type:
                continue
            if ent["label"] != "ACTION":
                non_verb_dbpedia_ids.add(id)
            else:
                verb_dbpedia_ids.add(id)

    if non_verb_dbpedia_ids.intersection(verb_dbpedia_ids):
        # default assume non verb
        verb_dbpedia_ids = verb_dbpedia_ids.difference(non_verb_dbpedia_ids)
    from app.models.dbpedia_entity_category import DBPediaEntityCategory

    queryset = DBPediaEntityCategory.objects(entity__in=non_verb_dbpedia_ids)

    entity_abstraction_updates = []

    entity_with_abstractions = set()
    for item in queryset:
        entity_with_abstractions.add(item.entity)
        if is_valid_abstraction(item.category):
            entity_abstraction_updates.append(
                {
                    "news_analytics": analytics.id,
                    "entity": item.entity,
                    "category": item.category,
                }
            )

    entities_with_no_abstraction = [
        dbpedia_id
        for dbpedia_id in non_verb_dbpedia_ids
        if dbpedia_id not in entity_with_abstractions
    ]
    for entity in entities_with_no_abstraction:
        entity_abstraction_updates.append(
            {
                "news_analytics": analytics.id,
                "entity": entity,
                "category": f"Entity:{entity}",
            }
        )
    for entity in verb_dbpedia_ids:
        entity_abstraction_updates.append(
            {
                "news_analytics": analytics.id,
                "entity": entity,
                "category": f"Action:{entity}",
            }
        )
    entities = list(verb_dbpedia_ids) + list(non_verb_dbpedia_ids)
    DocumentEntityCategory.objects(
        news_analytics=analytics.id, entity__nin=entities
    ).delete()
    DocumentEntity.objects(news_analytics=analytics.id, entity__nin=entities).delete()
    if entity_abstraction_updates:
        DocumentEntityCategory.upsert_many(entity_abstraction_updates)
        entity_updates = [
            {"news_analytics": analytics.id, "entity": item} for item in entities
        ]
        DocumentEntity.upsert_many(entity_updates)


def task_extract_document_abstraction(skip=0):
    """
    Extract entities from news_analytics
    results stored in DocumentEntity
    :param skip:
    :return:
    """
    query = Q(processing_state=NewsAnalyticsProcessingState.NAMED_ENTITY_LINKED.value)

    item = NewsAnalytics.objects(query).skip(skip).first()
    while item:
        _extract_document_entity_abstraction(item)
        item.processing_state = (
            NewsAnalyticsProcessingState.DOCUMENT_ABSTRACTION_EXTRACTED.value
        )
        item.save()
        print(f"done task_extract_document_abstraction {item.url}")
        item = NewsAnalytics.objects(query).skip(skip).first()
