from app.models.news_analytics import NewsAnalytics


def test_similar_news_by_abstraction():
    url = "20150302-100948000-nL5N0W41NV-1-2"
    url = "20150302-125028000-nD8N0VL01U-1-2"
    analytics = NewsAnalytics.objects(url=url.strip()).first()
    from datetime import datetime

    start = datetime.utcnow()
    res = analytics.similar_news_by_abstraction()
    delta1 = (datetime.utcnow() - start).total_seconds()

    start = datetime.utcnow()
    res = analytics.similar_news_by_abstraction_v2()
    delta2 = (datetime.utcnow() - start).total_seconds()
    pass


def test_all_abstraction_pairs():
    url = "https://seekingalpha.com/news/3353821-freeport-still-likely-sell-indonesia-assets-year-inalum-says"
    analytics = NewsAnalytics.objects(url=url.strip()).first()
    (
        abstraction_entity_map,
        abstraction_key_ontology_map,
    ) = analytics.all_abstraction_pairs()
    analytics.similar_news_by_entity()
    pass


def test_entity_abstraction_pruning():
    id = "5ee818b36bdf6f276139f802"
    analytics = NewsAnalytics.objects(id=id).first()
    data = analytics.spacy_json
    for ent in data.get("ents", []):
        ent


def test_migrate_entity_with_spaces():
    from app.models.news_analytics import NewsAnalytics, NewsAnalyticsProcessingState

    urls = [
        "https://seekingalpha.com/news/3327930-jd-com-take-amazon-europe",
        "https://seekingalpha.com/news/3168124-amazons-interest-office-depot-business-unit-stokes-merger-bets",
    ]

    res = NewsAnalytics.objects.aggregate(
        [
            # {
            #    "$match": {"url": {"$in": urls}}
            # },
            {
                "$project": {"url": 1, "spacy_json.ents.params.dbpedia_id": 1},
            },
            {
                "$group": {
                    "_id": "$_id",
                    "dbpedia_ids": {"$addToSet": "$spacy_json.ents.params.dbpedia_id"},
                }
            },
            {"$unwind": "$dbpedia_ids"},
            {"$unwind": "$dbpedia_ids"},
            {
                "$addFields": {
                    "result": {"$regexMatch": {"input": "$dbpedia_ids", "regex": " "}}
                }
            },
            {"$match": {"result": True}},
            {"$group": {"_id": "$_id", "dbpedia_ids": {"$addToSet": "$dbpedia_ids"}}},
        ]
    )
    res = list(res)
    ids = [item["_id"] for item in res]
    NewsAnalytics.objects(id__in=ids).update(
        set__processing_state=NewsAnalyticsProcessingState.NAMED_ENTITY_LINKED.value
    )
