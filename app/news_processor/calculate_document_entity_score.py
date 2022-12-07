import math

from mongoengine import Q

from app.models.document_entity_category import DocumentEntityCategory
from app.models.news_analytics import NewsAnalytics, NewsAnalyticsProcessingState


def task_batch_calculate_entity_tfidf_score(skip=0):
    from app.models.document_entity import DocumentEntity

    total_document_count = NewsAnalytics.objects.count()
    item = DocumentEntity.objects(entity_tfidf_score=None).first()
    while item:
        print(item)
        entity = item.entity
        key = entity.split(":")[-1]
        entity_documents = DocumentEntity.objects(entity=entity)
        idf = math.log10(total_document_count / len(entity_documents))
        for document_entity in entity_documents.filter(entity_tfidf_score=None):
            tf = 0
            for ent in document_entity.news_analytics.spacy_json.get("ents", []):
                if not ent["params"].get("dbpedia_id", ""):
                    continue
                if ent["params"].get("dbpedia_id", "").find(key) > -1:
                    tf += 1
            entity_tf_idf = (
                tf
                / len(document_entity.news_analytics.spacy_json.get("tokens", []))
                * idf
            )
            document_entity.entity_tfidf_score = round(entity_tf_idf, 3)
            document_entity.save()
            DocumentEntityCategory.objects(
                news_analytics=document_entity.news_analytics.id,
                entity=document_entity.entity,
            ).update(set__entity_relevance_score=document_entity.entity_tfidf_score)

        item = DocumentEntity.objects(entity_tfidf_score=None).first()
    query = Q(
        processing_state=NewsAnalyticsProcessingState.DOCUMENT_ABSTRACTION_EXTRACTED.value
    )
    NewsAnalytics.objects(query).update(
        set__processing_state=NewsAnalyticsProcessingState.DOCUMENT_ENTITY_SCORE_CALCULATED.value
    )
