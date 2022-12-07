from mongoengine import Q

from app.models.document_pattern import DocumentPattern, DocumentPatternProcessingState
from app.models.news_analytics import NewsAnalytics, NewsAnalyticsProcessingState


def _register_document_seed_patterns(url_or_news_analytics):
    from app.models.dbpedia_category import DBPediaCategory
    from app.models.document_entity import DocumentEntity
    from app.models.document_entity_category import DocumentEntityCategory
    from app.models.news_analytics import NewsAnalytics

    # select candidates
    analytics = url_or_news_analytics
    if not hasattr(url_or_news_analytics, "id"):
        analytics = NewsAnalytics.objects(url=url_or_news_analytics).first()

    from collections import defaultdict

    entity_abstraction_map = defaultdict(list)
    document_category_queryset = (
        DocumentEntityCategory.objects(
            news_analytics=analytics.id,
            concept_relevance_score__gt=0.5,
            total_relevance_score=None,
        )
        .no_dereference()
        .order_by("-concept_relevance_score")
    )
    for item in document_category_queryset:
        entity_abstraction_map[item.entity].append(item)

    entity_queryset = list(
        DocumentEntity.objects(
            news_analytics=analytics.id, entity__in=list(entity_abstraction_map.keys())
        )
        .no_dereference()
        .order_by("-entity_tfidf_score")
    )

    specificity_score_queryset = DBPediaCategory.objects(
        name__in=document_category_queryset.distinct("category")
    )
    specificity_map = dict()
    for item in specificity_score_queryset:
        specificity_map[item.name] = item.specificity_score

    for item in entity_queryset:
        entity = item.entity
        entity_relevance_score = item.entity_tfidf_score
        assert entity_relevance_score
        for abstraction in entity_abstraction_map.get(entity):
            abstraction_relevance_score = abstraction.concept_relevance_score
            abstraction.entity_relevance_score = round(entity_relevance_score, 3)
            specificity_score = specificity_map[abstraction.category]
            if not specificity_score:
                print(abstraction.category)
            assert specificity_score
            abstraction.total_relevance_score = round(
                entity_relevance_score
                * abstraction_relevance_score
                * specificity_score,
                3,
            )
            abstraction.save()

    document_categories = DocumentEntityCategory.objects(
        news_analytics=analytics.id, total_relevance_score__gte=0.1 * 0.5
    ).distinct("category")

    existing_patterns = DocumentPattern.objects(
        name__in=list(document_categories), category_count=1
    ).distinct("name")

    updates = []
    for new_pattern in set(document_categories).difference(set(existing_patterns)):
        updates.append(
            {
                "name": new_pattern,
                "categories": [new_pattern],
                "category_count": 1,
                "processing_state": DocumentPatternProcessingState.DOCUMENTS_OUTDATED.value,
            }
        )
    if updates:
        res = DocumentPattern.upsert_many(updates)

    # invalidate patterns with category count greater than 1
    # res = DocumentPattern.objects(
    #    categories__in=document_categories, documents__nin=[str(analytics.id)]
    # ).update(
    #    set__processing_state=DocumentPatternProcessingState.DOCUMENTS_OUTDATED.value,
    #    add_to_set__documents=[str(analytics.id)],
    # )
    return document_categories


def task_register_document_seed_patterns(skip=0):
    query = Q(
        processing_state=NewsAnalyticsProcessingState.DOCUMENT_ENTITY_ABSTRACTION_SCORE_CALCULATED.value
    )
    item = NewsAnalytics.objects(query).skip(skip).first()
    while item:
        _register_document_seed_patterns(item)
        item.processing_state = (
            NewsAnalyticsProcessingState.DOCUMENT_SEED_PATTERN_REGISTERED.value
        )
        item.save()
        print(f"done _calculate_document_abstraction_similar_news {item.url}")
        item = NewsAnalytics.objects(query).skip(skip).first()
