import requests
from flask import Blueprint, current_app, jsonify, request
from mongoengine import Q

services = Blueprint("news_search", __name__)


def test_data(keywords):
    import bson

    from app.models.dbpedia_entity_category import DBPediaEntityCategory
    from app.models.news_analytics import NewsAnalytics

    res = dict()
    res["entities"] = dict()
    if not keywords:
        keywords = "5eeaac39f97761a2e1d359fe"
    is_object_id = bson.objectid.ObjectId.is_valid(keywords)
    if not is_object_id:
        nel_url = current_app.config["NEL_ENDPOINT"]

        resp = requests.post(url=nel_url, data={"input-text": keywords}).json()
        print(resp)
        res["entity_html"] = resp["html"]
        prefix = current_app.config["DBPEDIA_PREFIX"]
        entities = [
            item["params"]["dbpedia_id"].split(prefix)[-1]
            for item in resp["ents"]
            if item["params"]["dbpedia_id"]
        ]
        queryset = DBPediaEntityCategory.objects(entity__in=entities)
        for entity in entities:
            abstractions = queryset.filter(entity=entity).distinct("category")
            res["entities"][entity] = abstractions
    else:
        news_analytics = NewsAnalytics.objects(Q(id=keywords)).first()

        res["entity_html"] = news_analytics.entity_html
        res["url"] = news_analytics.url
        res["id"] = str(news_analytics.id)
        entity_abstractions = news_analytics.entity_abstractions
        for entity, document_entity_categories in entity_abstractions.items():
            abstractions = [item["category"] for item in document_entity_categories]
            res["entities"][entity] = abstractions

    abstraction_entity_map = dict()
    for entity, abstractions in res["entities"].items():
        for abstraction in abstractions:
            abstraction_entity_map[abstraction] = entity
    from app.news_search.search_by_abstraction import get_news_by_abstractions

    print(abstraction_entity_map)
    pattern_map_sorted, documents2 = get_news_by_abstractions(
        url_or_news_analytics=None,
        abstraction_entity_map=abstraction_entity_map,
        news_ids_to_exclude=None if keywords else [res["id"]],
    )
    res["patterns"] = list(pattern_map_sorted.values())
    similar_results = []
    for item in documents2:
        analytics = item["document"]
        abstractions = []
        for abstraction, entities in item["matches"].items():
            for entity in entities:
                abstractions.append(
                    {
                        "abstraction": abstraction,
                        "match": entity["match"],
                        "original": entity["original"],
                    }
                )
        similar_results.append(
            {
                "abstractions": abstractions,
                "entity_html": analytics.entity_html,
                "id": str(analytics.id),
                "url": analytics.url,
            }
        )

    res["similar_results"] = similar_results
    return res


@services.route("/ping")
@services.route("/ping/")
@services.route("/ping/<string:key_words>")
def ping(key_words=None):
    print(key_words)
    res = test_data(key_words)
    return jsonify(res)


@services.route("/search_news_by_abstractions", methods=["POST"])
def search_news_by_abstraction():
    data = request.json
    from app.news_search.search_by_abstraction import get_news_by_abstractions

    entity_abstraction_map = data["entity_abstraction_map"]
    ids_to_exclude = data.get("news_ids_to_exclude", [])
    abstraction_entity_map = dict()
    for key, val in entity_abstraction_map.items():
        abstraction_entity_map[val] = key
    print(data)
    pattern_map_sorted, documents2 = get_news_by_abstractions(
        url_or_news_analytics=None,
        abstraction_entity_map=abstraction_entity_map,
        news_ids_to_exclude=ids_to_exclude,
    )

    res = []
    for item in documents2:
        analytics = item["document"]
        abstractions = []
        for abstraction, entities in item["matches"].items():
            for entity in entities:
                abstractions.append(
                    {
                        "abstraction": abstraction,
                        "match": entity["match"],
                        "original": entity["original"],
                    }
                )
        res.append(
            {
                "abstractions": abstractions,
                "entity_html": analytics.entity_html,
                "id": str(analytics.id),
                "url": analytics.url,
            }
        )

    return jsonify(res)
