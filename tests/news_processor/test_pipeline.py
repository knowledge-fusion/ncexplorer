from app.models.document_entity_category import DocumentEntityCategory


def test_pipeline():
    from app.news_processor.calculate_document_entity_abstraction_score import (
        task_calculate_document_entity_abstraction_score,
    )
    from app.news_processor.calculate_document_entity_score import (
        task_batch_calculate_entity_tfidf_score,
    )
    from app.news_processor.extract_document_entity_abstraction import (
        task_extract_document_abstraction,
    )
    from app.news_processor.named_entity_linking import task_named_entity_linking
    from app.news_processor.register_document_seed_patterns import (
        task_register_document_seed_patterns,
    )

    task_named_entity_linking()

    task_extract_document_abstraction()
    task_batch_calculate_entity_tfidf_score()

    task_calculate_document_entity_abstraction_score()
    task_register_document_seed_patterns()


def test_document_pipeline():
    from app.models.news_analytics import NewsAnalytics
    from app.news_processor.calculate_document_entity_abstraction_score import (
        _document_entity_abstraction_score,
    )

    url = "  https://seekingalpha.com/news/3168124-amazons-interest-office-depot-business-unit-stokes-merger-bets "

    news_analytics = NewsAnalytics.objects(url=url.strip()).first()

    from app.news_processor.calculate_document_entity_score import (
        _calculate_document_entity_score,
    )

    _calculate_document_entity_score(news_analytics)
    _document_entity_abstraction_score(news_analytics=news_analytics)


def test_copy_corpus_entity_count():
    pipeline = [
        {
            "$group": {
                "_id": "$category",
                "entities": {"$addToSet": "$entity"},
            }
        },
        {
            "$project": {
                "name": "$_id",
                "entity_count": {"$size": "$entities"},
            }
        },
    ]
    res = DocumentEntityCategory.objects.aggregate(pipeline)
    updates = []
    for item in res:
        updates.append(
            {"name": item["_id"], "corpus_entity_count": int(item["entity_count"])}
        )
    from app.models.dbpedia_category import DBPediaCategory

    if updates:
        res = DBPediaCategory.upsert_many(updates)


def test_copy_kg_entity_count():
    from app.models.dbpedia_category import DBPediaCategory
    from app.models.dbpedia_entity_category import DBPediaEntityCategory

    queryset = DBPediaCategory.objects(kg_entity_count=None).limit(10000)
    while queryset:
        names = [item.name for item in queryset]
        pipeline = [
            {"$match": {"category": {"$in": names}}},
            {
                "$group": {
                    "_id": "$category",
                    "entities": {"$addToSet": "$entity"},
                }
            },
            {
                "$project": {
                    "name": "$_id",
                    "entity_count": {"$size": "$entities"},
                }
            },
        ]
        res = DBPediaEntityCategory.objects.aggregate(pipeline)
        updates = []
        for item in res:
            updates.append(
                {"name": item["_id"], "kg_entity_count": int(item["entity_count"])}
            )

        if updates:
            res = DBPediaCategory.upsert_many(updates)
            queryset = DBPediaCategory.objects(kg_entity_count=None).limit(10000)
