import math

from mongoengine import Q


def _find_expansion_candidates(document_entity_categories):
    from app.models.dbpedia_category import DBPediaCategoryHierarchy

    categories = [item.category for item in document_entity_categories]
    res = dict()
    parents_queryset = DBPediaCategoryHierarchy.objects(name__in=categories)
    for document_entity_category in document_entity_categories:
        res[document_entity_category] = res.get(document_entity_category, {})
        for item in parents_queryset.filter(name=document_entity_category.category):
            parent = item.parent
            siblings = DBPediaCategoryHierarchy.objects(parent=parent).distinct("name")
            res[document_entity_category][parent] = siblings

    return res


def _expand_abstractions(news_analytics, document_entity_categories_to_expand):
    from app.models.document_entity_category import DocumentEntityCategory
    from app.news_processor.calculate_document_entity_abstraction_score import (
        _document_entity_abstraction_score,
    )

    existing_categories = DocumentEntityCategory.objects(
        news_analytics=news_analytics.id
    ).distinct("category")
    expansion_candidates = _find_expansion_candidates(
        document_entity_categories_to_expand
    )
    updates = []
    for document_entity_category, neighbors in expansion_candidates.items():
        for parent in list(neighbors.keys()):
            if parent in existing_categories:
                continue
            updates.append(
                {
                    "news_analytics": document_entity_category.news_analytics.id,
                    "entity": document_entity_category.entity,
                    "category": parent,
                    "expansion_routes": list(document_entity_category.expansion_routes)
                    + [document_entity_category.category],
                }
            )

    abstractions_boost_parent_connectivity_scores = []
    if updates:
        res = DocumentEntityCategory.upsert_many([item.copy() for item in updates])
        upserted_ids = [item["_id"] for item in res["upserted"]]
        _document_entity_abstraction_score(news_analytics)
        new_document_entity_categories = DocumentEntityCategory.objects(
            news_analytics=news_analytics.id, id__in=upserted_ids
        )
        for new_document_entity_category in new_document_entity_categories:
            parent = new_document_entity_category.expansion_routes[-1]
            parent_document_category = document_entity_categories_to_expand.filter(
                category=parent, entity=new_document_entity_category.entity
            ).first()
            parent_score = parent_document_category.concept_relevance_score

            siblings = expansion_candidates[parent_document_category][
                new_document_entity_category.category
            ]
            expansion_concept_drift = math.pow(0.95, len(siblings))
            new_document_entity_category.concept_relevance_score *= (
                expansion_concept_drift
            )
            new_document_entity_category.save()
            if new_document_entity_category.concept_relevance_score >= parent_score:
                abstractions_boost_parent_connectivity_scores.append(
                    new_document_entity_category.id
                )
    abstractions_boost_parent_connectivity_scores = DocumentEntityCategory.objects(
        id__in=abstractions_boost_parent_connectivity_scores
    )
    return abstractions_boost_parent_connectivity_scores


def _document_entity_abstraction_expansion_score(news_analytics):
    from app.models.document_entity import DocumentEntity
    from app.models.document_entity_category import DocumentEntityCategory

    document_entities = DocumentEntity.objects(
        news_analytics=news_analytics.id
    ).no_dereference()
    document_entity_categories = DocumentEntityCategory.objects(
        news_analytics=news_analytics.id,
        concept_relevance_score__ne=None,
    ).no_dereference()
    abstraction_scores = dict()
    for document_entity_category in document_entity_categories:
        document_entity = document_entities.filter(
            entity=document_entity_category.entity
        ).first()
        score = (
            document_entity.entity_tfidf_score
            * document_entity_category.concept_relevance_score
        )
        abstraction_scores[document_entity_category] = score

    from numpy import average

    average_score = average(list(abstraction_scores.values()))
    threshold = max(average_score, 0.1 * 0.3)
    document_entity_categories_to_expand = []
    for document_entity_category, score in abstraction_scores.items():
        if score >= threshold:
            document_entity_categories_to_expand.append(document_entity_category.id)

    document_entity_categories_to_expand = DocumentEntityCategory.objects(
        id__in=document_entity_categories_to_expand
    )
    while document_entity_categories_to_expand:
        document_entity_categories_to_expand = _expand_abstractions(
            news_analytics, document_entity_categories_to_expand
        )
    print(document_entity_categories_to_expand)
    return True


def task_calculate_document_entity_abstraction_expansion_score(skip=0):
    from app.models.news_analytics import NewsAnalytics, NewsAnalyticsProcessingState

    query = Q(
        processing_state=NewsAnalyticsProcessingState.DOCUMENT_ENTITY_ABSTRACTION_SCORE_CALCULATED.value,
    )

    item = NewsAnalytics.objects(query).skip(skip).first()
    while item:
        print(
            f"start task_calculate_document_entity_abstraction_expansion_score {skip} {item.url}"
        )
        _document_entity_abstraction_expansion_score(item)

        item.processing_state = (
            NewsAnalyticsProcessingState.DOCUMENT_ENTITY_ABSTRACTION_EXPANSION_SCORE_CALCULATED.value
        )
        item.save()

        item = NewsAnalytics.objects(query).skip(skip).first()
