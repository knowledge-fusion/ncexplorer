def get_news_by_entities(dbpedia_ids, news_ids_to_exclude=None, limit=None):
    from app.models.document_entity_category import DocumentEntityCategory

    # from app.models.wiki_data_entity import WikiDataEntity
    from app.models.news_analytics import NewsAnalytics

    pipeline = [
        {"$match": {"entity": {"$in": dbpedia_ids}}},
        {
            "$group": {
                "_id": "$news_analytics",
                "entity_ids": {"$addToSet": "$entity"},
            }
        },
        {
            "$project": {
                "_id": 1,
                "entity_ids": 1,
                "num_entity": {"$size": "$entity_ids"},
            }
        },
        {"$sort": {"num_entity": -1}},
    ]
    if limit:
        pipeline.append({"$limit": limit})
    queryset = DocumentEntityCategory.objects().aggregate(pipeline)

    result = []
    document_ids = []
    entity_dbpedia_ids = []
    for item in queryset:
        result.append(item)
        document_ids.append(item["_id"])
        entity_dbpedia_ids += item["entity_ids"]

    news_result = NewsAnalytics.objects(id__in=document_ids)
    if news_ids_to_exclude:
        news_result = news_result.filter(id__nin=news_ids_to_exclude)
    prefix = "http://dbpedia.org/resource/"

    news_map = {news.id: news for news in news_result}
    res = []
    for item in result:
        if news_map.get(item["_id"]):
            item["document"] = news_map[item["_id"]]
            item["entities"] = item["entity_ids"]
            res.append(item)
    return res
