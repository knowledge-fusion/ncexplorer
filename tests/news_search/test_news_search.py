def test_search_by_abstraction(app):
    import json

    with app.test_client() as versioned_user_agent:
        url = "/search_news_by_abstractions"
        abstractions = [
            "http://dbpedia.org/ontology/SportsEvent",
            "http://schema.org/Event",
            "http://dbpedia.org/ontology/Politician",
            "http://dbpedia.org/resource/Category:Environmental_issues",
            "http://dbpedia.org/resource/Category:Activism_by_type",
        ]
        resp = versioned_user_agent.open(
            url, method="POST", json={"abstractions": abstractions}
        )
        data = json.loads(resp.data)
        return data


def test_find_similar_news():
    from app.models.news_analytics import NewsAnalytics

    analytics = NewsAnalytics.objects().first()
    res = analytics.similar_news()


def test_news_search(app):
    with app.test_client() as versioned_user_agent:
        url = "/ping/5eea6121f97761a2e1d342f3"
        resp = versioned_user_agent.open(url, method="GET")
        data = resp.json
        assert data


def test_get_news_by_abstractions_v2(app):
    from app.news_search.search_by_abstraction import get_news_by_abstractions_v2

    url = "20150301-002719000-nL5N0W20RR-1-2"
    pattern, documents = get_news_by_abstractions_v2(url.strip())
    documents


def test_get_news_by_entities(app):
    from app.models.news_analytics import NewsAnalytics

    url = " 20150301-004000000-nL4N0W3009-1-2 "
    news_analytics = NewsAnalytics.objects(url=url.strip()).first()

    res = news_analytics.similar_news_by_entity()
    # res2 = news_analytics.similar_news_by_abstraction()
    res


def test_calculate_document_abstraction_task():
    from app.news_search.tasks import calculate_document_search_result_task

    calculate_document_search_result_task()


def test_get_news_by_abstractions():
    from app.news_search.search_by_abstraction import (
        get_news_by_abstractions,
        get_news_by_abstractions_v2,
    )

    url = " https://6thfloor.blogs.nytimes.com/2011/05/02/osamas-long-goodbye/ "
    url = "  20150301-004000000-nL4N0W3009-1-2  "
    url = "20150302-125028000-nD8N0VL01U-1-2"
    url = "	https://seekingalpha.com/news/3347038-e-trade-minus-2_6-percent-big-quarter"
    pattern_map, res = get_news_by_abstractions(url.strip(), news_ids_to_exclude=[])
    """
    pattern_map2, res2 = get_news_by_abstractions_v2(
        url.strip(), news_ids_to_exclude=["5ee7a77938c9d3c642344824"]
    )
    """
    pass


def test_search_news_by_abstraction():
    data = dict()
    ids_to_exclude = data.get("news_ids_to_exclude", [])
    url = "20150302-101142000-nFWN0W403P-1-2"
    from app.news_search.search_by_abstraction import get_news_by_abstractions

    pattern_map_sorted, documents2 = get_news_by_abstractions(
        url_or_news_analytics=url.strip(), news_ids_to_exclude=ids_to_exclude
    )

    res = []
    for item in documents2:
        print(item)
        analytics = item["document"]
        abstractions = []
        for abstraction, entity in item["matches"].items():
            abstractions.append(f"{abstraction} {entity}")
        res.append(
            {
                "abstractions": abstractions,
                "entity_html": analytics.entity_html,
                "id": str(analytics.id),
                "url": analytics.url,
            }
        )

    res


def test_pattern_matching():
    from bson import ObjectId

    matching_news = [
        {
            "abstraction": "http://dbpedia.org/resource/Category:Member_states_of_the_United_Nations",
            "entity_id": ObjectId("5e7cd1b500efd1783e1a61a0"),
        },
        {
            "abstraction": "http://yago-knowledge.org/resource/Sovereign_state",
            "entity_id": ObjectId("5e7cd1b500efd1783e1a61a0"),
        },
        {
            "abstraction": "http://schema.org/Country",
            "entity_id": ObjectId("5e7cd1b500efd1783e1a61a0"),
        },
        {
            "abstraction": "http://dbpedia.org/resource/Category:Language_and_nationality_disambiguation_pages",
            "entity_id": ObjectId("5fb6242778ea3e312b097715"),
        },
    ]
    matching_abstractions = dict()
    for item in matching_news:
        pass
    original_news = {
        "http://dbpedia.org/resource/Category:Language_and_nationality_disambiguation_pages": "Egyptian",
        "http://dbpedia.org/resource/Category:Member_states_of_the_African_Union": "Egypt",
        "http://dbpedia.org/resource/Category:Countries_in_Africa": "Egypt",
        "http://dbpedia.org/resource/Category:Member_states_of_the_Organisation_internationale_de_la_Francophonie": "Egypt",
        "http://dbpedia.org/resource/Category:Saharan_countries": "Egypt",
        "http://dbpedia.org/resource/Category:Countries_in_Asia": "Egypt",
        "http://dbpedia.org/resource/Category:Western_Asian_countries": "Egypt",
        "http://dbpedia.org/resource/Category:Member_states_of_the_Organisation_of_Islamic_Cooperation": "Egypt",
        "http://dbpedia.org/resource/Category:Middle_Eastern_countries": "Egypt",
        "http://dbpedia.org/resource/Category:Near_Eastern_countries": "Egypt",
        "http://dbpedia.org/resource/Category:Developing_8_Countries_member_states": "Egypt",
        "http://dbpedia.org/resource/Category:Member_states_of_the_United_Nations": "Egypt",
        "http://dbpedia.org/resource/Category:Member_states_of_the_Arab_League": "Egypt",
        "http://dbpedia.org/resource/Category:Arabic-speaking_countries_and_territories": "Egypt",
        "http://yago-knowledge.org/resource/Sovereign_state": "Egypt",
        "http://dbpedia.org/resource/Category:G15_nations": "Egypt",
        "http://dbpedia.org/resource/Category:Member_states_of_the_Union_for_the_Mediterranean": "Egypt",
        "http://schema.org/Country": "Egypt",
        "http://dbpedia.org/resource/Category:Transcontinental_countries": "Egypt",
        "http://dbpedia.org/resource/Category:North_African_countries": "Egypt",
        "http://dbpedia.org/resource/Category:Eastern_Mediterranean": "Egypt",
        "http://dbpedia.org/resource/Category:1922_establishments_in_Africa": "Egypt",
        "http://dbpedia.org/resource/Category:States_and_territories_established_in_1922": "Egypt",
        "http://dbpedia.org/resource/Category:1922_establishments_in_Asia": "Egypt",
    }


def test_test_data():
    from app.models.news_analytics import NewsAnalytics

    news_id = None
    from mongoengine import Q

    query = Q(version=19)
    if news_id:
        query &= Q(id=news_id)
    else:
        query &= Q(id="5eea9bb5f97761a2e1d35515")
    news_analytics = NewsAnalytics.objects(query).first()
    res = dict()
    res["entity_html"] = news_analytics.entity_html
    res["url"] = news_analytics.url
    res["id"] = str(news_analytics.id)
    res["entities"] = dict()
    entity_abstractions = news_analytics.entity_abstractions
    for entity, document_entity_categories in entity_abstractions.items():
        abstractions = [item["category"] for item in document_entity_categories]
        res["entities"][entity] = abstractions

    print(res["entities"])

    return res
