import itertools
import json
import math


def pattern_score(key, news_ids):
    val = math.log2(len(key.split(",")) + 0.1) * math.log10(len(news_ids) + 0.1)
    return val


# @cache.memoize()


def get_news_by_abstractions(
    url_or_news_analytics, abstraction_entity_map=None, news_ids_to_exclude=None
):
    from datetime import datetime

    from app.models.document_entity_category import DocumentEntityCategory
    from app.models.news_analytics import NewsAnalytics

    start = datetime.utcnow()
    print(0)
    analytics = url_or_news_analytics
    if isinstance(url_or_news_analytics, str) and (
        not hasattr(url_or_news_analytics, "id")
    ):
        analytics = NewsAnalytics.objects(url=url_or_news_analytics).first()
        queryset = DocumentEntityCategory.objects(news_analytics=analytics.id)
        abstraction_entity_map = dict()
        for item in queryset:
            abstraction_entity_map[item.category] = item.entity

    print(f"1 { (datetime.utcnow() - start).total_seconds()}")
    pipeline = [
        {
            "$match": {
                "category": {"$in": list(abstraction_entity_map.keys())},
                # "total_relevance_score": {"$gte": 0.1},
            }
        },
        {
            "$group": {
                "_id": "$news_analytics",
                "categories": {"$addToSet": "$category"},
                "entities": {
                    "$addToSet": "$entity"
                },  # abstraction need to map to different entity
                "ordered_categories": {"$push": "$category"},
                "ordered_entities": {"$push": "$entity"},
                "relevance_scores": {"$push": "$total_relevance_score"},
            }
        },
        {
            "$project": {
                "_id": 1,
                "categories": 1,
                "entities": 1,
                "ordered_categories": 1,
                "ordered_entities": 1,
                "num_category": {"$size": "$categories"},
                "num_entity": {"$size": "$entities"},
                "total_relevance_score": {"$sum": "$relevance_scores"},
            }
        },
        {
            "$match": {
                "num_category": {"$eq": len(abstraction_entity_map.keys())},
                "num_entity": {"$gte": len(abstraction_entity_map.keys())},
            }
        },
    ]

    queryset = DocumentEntityCategory.objects().aggregate(pipeline)
    print(f"2 { (datetime.utcnow() - start).total_seconds()}")
    result = {}
    entity_ids = []
    prefix = "http://dbpedia.org/resource/"

    print(queryset)
    for item in queryset:
        val = dict()
        for idx, category in enumerate(item["ordered_categories"]):
            # must come from different entities
            entity = item["ordered_entities"][idx]
            val[entity] = category
            entity_ids.append(prefix + entity)

        result[item["_id"]] = val

    news_result = NewsAnalytics.objects(id__in=list(result.keys())[0:5])
    if news_ids_to_exclude:
        news_result = news_result.filter(id__nin=news_ids_to_exclude)

    res = []
    pattern_map = {}
    for news in news_result:
        matches = dict()
        entity_abstraction_m = dict()
        for entity_id, abstraction in result[news.id].items():
            matches[abstraction] = matches.get(abstraction, [])
            matches[abstraction].append(
                {
                    "match": entity_id,
                    "original": abstraction_entity_map[abstraction],
                }
            )
            original_entity = abstraction_entity_map[abstraction]
            entity_abstraction_m[original_entity] = entity_abstraction_m.get(
                original_entity, []
            )
            entity_abstraction_m[original_entity].append(abstraction)

        patterns = set()
        for combination in itertools.product(*list(entity_abstraction_m.values())):
            combination = list(combination)
            combination.sort()
            pattern_key = ",".join(combination)
            patterns.add(pattern_key)
            pattern_map[pattern_key] = pattern_map.get(
                pattern_key,
                {
                    "documents": {analytics.id} if analytics else set(),
                    "categories": combination,
                    "name": ",".join(combination),
                    "category_count": len(combination),
                },
            )
            pattern_map[pattern_key]["documents"].add(news.id)

        item = {
            "id": str(news.id),
            "document": news,
            "matches": matches,
            "patterns": list(patterns),
        }
        res.append(item)

    from app.models.document_pattern import DocumentPattern

    print(f"3 { (datetime.utcnow() - start).total_seconds()}")

    if analytics:
        pattern_scores = DocumentPattern.objects(
            name__in=list(pattern_map.keys()), documents__in=[analytics.id]
        ).exclude("created_at")
        existing_keys = pattern_scores.distinct("name")
        missing_keys = set(pattern_map.keys()).difference(set(existing_keys))
        extra_keys = set(existing_keys).difference(set(pattern_map.keys()))
        if extra_keys:
            DocumentPattern.objects(name__in=list(extra_keys)).update(
                pull__documents=analytics.id
            )
        if missing_keys:
            print(f"missing keys {missing_keys}")
            updates = []
            for key in missing_keys:
                value = pattern_map[key]
                value["documents"] = list(value["documents"])
                if analytics and str(analytics.id) not in value["documents"]:
                    value["documents"].append(str(analytics.id))
                value["document_count"] = len(value["documents"])
                updates.append(value)
            DocumentPattern.upsert_many(updates)

    print(f"4 { (datetime.utcnow() - start).total_seconds()}")

    pattern_scores = DocumentPattern.objects(name__in=list(pattern_map.keys()))

    print(f"5 { (datetime.utcnow() - start).total_seconds()}")

    for key, val in pattern_map.items():
        val["documents"] = [str(item) for item in val["documents"]]
        val["document_count"] = len(val["documents"])
        score = pattern_scores.filter(name=val["name"]).first()
        if not score:
            continue
        score_json = json.loads(score.to_json())
        score_json.pop("created_at", None)
        score_json.pop("updated_at", None)
        score_json.pop("documents")
        val["id"] = score_json.pop("_id")["$oid"]
        val.update(score_json)
    print(f"5.5 { (datetime.utcnow() - start).total_seconds()}")

    pattern_map_sorted = {
        k: v
        for k, v in sorted(
            pattern_map.items(),
            key=lambda item: item[1].get("kg_connectivity_sample_10", 0),
            reverse=True,
        )
    }

    res.sort(
        key=lambda item: sum(
            pattern_map[p].get("kg_connectivity2_diversity", 0)
            for p in item["patterns"]
        )
        * 100
        + len(item["patterns"][0].split(",")) * 100
        + len(item["patterns"]) * 10
        + len(matches)
        - pattern_map[item["patterns"][0]]["document_count"],
        reverse=True,
    )
    print(f"6 { (datetime.utcnow() - start).total_seconds()}")

    return pattern_map_sorted, res


def get_news_by_abstractions_v2(url_or_news_analytics, news_ids_to_exclude=None):
    from app.models.document_pattern import DocumentPattern
    from app.models.news_analytics import NewsAnalytics

    analytics = url_or_news_analytics
    if not hasattr(url_or_news_analytics, "id"):
        analytics = NewsAnalytics.objects(url=url_or_news_analytics).first()

    res = DocumentPattern.objects(documents__in=[analytics.id])
    pattern_map = dict()
    document_pattern_map = dict()
    for item in res:
        item_json = json.loads(item.to_json())
        pattern_map[item.name] = {
            "documents": item.documents,
            "categories": item.categories,
            "name": item.name,
            "category_count": item.category_count,
            "document_count": item.document_count,
        }
        for document in item.documents:
            document_pattern_map[document.id] = document_pattern_map.get(
                document.id,
                {
                    "id": str(document.id),
                    "document": document,
                    "matches": dict(),
                    "patterns": [],
                },
            )
            document_pattern_map[document.id]["patterns"].append(item.name)
            for category in item.name.split(","):
                document_pattern_map[document.id]["matches"][category] = []
    if news_ids_to_exclude:
        for id in news_ids_to_exclude:
            document_pattern_map.pop(id, None)

    from app.models.document_entity_category import DocumentEntityCategory

    queryset = DocumentEntityCategory.objects(
        news_analytics__in=list(document_pattern_map.keys())
    )
    for document_id, val in document_pattern_map.items():
        for category in val["matches"].keys():
            for entity in queryset.filter(
                news_analytics=document_id, category=category
            ):
                val["matches"][category].append(entity)

    pattern_map_sorted = {
        k: v
        for k, v in sorted(
            pattern_map.items(),
            key=lambda item: item[1].get("kg_connectivity_sample_10", 0),
            reverse=True,
        )
    }

    return pattern_map_sorted, list(res)
