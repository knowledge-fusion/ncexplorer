import json
import uuid
from collections import defaultdict

from flask import Blueprint, jsonify, request
from mongoengine import Q

from app.extenstions import cache
from app.models.document_pattern import DocumentPattern
from app.models.document_pattern_evaluation import (
    DocumentPatternEvaluation,
    DocumentPatternEvaluationQuestion,
)

services = Blueprint("pattern_explore", __name__)


@cache.memoize(timeout=60)
def trending_patterns():
    names = DocumentPatternEvaluationQuestion.objects.distinct("name")
    res = [name.split(",") for name in names]
    print(res)
    return res


@services.route("/load_random_pattern")
def load_random_pattern():
    from random import sample

    names = trending_patterns()
    sampled_names = []
    sampled_names.append(
        ["Category:Mass_media_in_the_United_States", "Category:American_billionaires"]
    )
    sampled_names.append(["Category:Countries_in_Europe", "Category:Conflicts"])

    sampled_names += sample(names, k=5)

    return jsonify(sampled_names)


@services.route("/subscribe_pattern/<string:email>/<string:pattern>", methods=["POST"])
def subscribe_pattern(email, pattern):
    print(email)
    print(pattern)
    from app.models.document_pattern_subscription import DocumentPatternSubscription

    res = DocumentPatternSubscription.upsert({"email": email, "name": pattern})
    print(res)
    return jsonify({"res": res})


@cache.memoize()
def _entities():
    from app.models.document_entity_category import DocumentEntityCategory

    entities = DocumentEntityCategory.objects(
        Q(concept_relevance_score__gt=0.1)
    ).distinct("entity")
    entities = [{"entity": item, "label": item.lower()} for item in entities]
    return entities


@services.route("/search_entity/<string:key_words>")
def search_entity(key_words=None):
    key_words = key_words.replace(" ", "_").lower()
    print(key_words)
    candidates = _entities()
    entities = [
        item["entity"] for item in candidates if item["label"].find(key_words) > -1
    ]

    entities.sort(
        key=len,
    )
    return jsonify(entities)


@services.route("/search_entity_or_abstraction/<string:key_words>")
def search_entity_or_abstraction(key_words=None):
    key_words = key_words.replace(" ", "_")
    print(key_words)

    from app.models.document_entity_category import DocumentEntityCategory

    res = DocumentEntityCategory.objects(
        Q(entity__icontains=f"{key_words}")
        | Q(category__istartswith=f"Category:{key_words}")
    )

    candidates = []
    for item in res:
        if item.entity.lower().find(key_words.lower()) > -1:
            candidates.append(item.entity)
        else:
            candidates.append(item.category)

    candidates.sort(
        key=len,
    )
    return jsonify(list(set(candidates)))


@services.route("/search_pattern/<string:key_words>")
def search_abstraction(key_words=None):
    key_words = key_words.replace(" ", "_")
    print(key_words)

    from app.models.document_entity_category import DocumentEntityCategory

    res = DocumentEntityCategory.objects(
        category__istartswith=f"Category:{key_words}"
    ).distinct("category")

    res.sort(
        key=len,
    )
    return jsonify(list(res))


@services.route("/related_term/<string:patterns>")
# @cache.memoize()
def related_term(patterns):
    from time import sleep

    from app.common.models import SystemConfig
    from app.models.dbpedia_entity_category import DBPediaEntityCategory
    from app.models.document_entity_category import DocumentEntityCategory

    terms = [item.strip() for item in patterns.split("|")]

    categories = [item for item in terms if item.find("Category:") > -1]
    entities = [item for item in terms if item.find("Category:") == -1]
    print(f"{categories=},{entities=}")

    categories.sort()
    entities.sort()
    key = "pattern-documents-" + "|".join(categories) + "|".join(entities)
    res = SystemConfig.objects(key=key).first()
    while not res:
        sleep(1)
        print("wait for document_id")
        res = SystemConfig.objects(key=key).first()

    res = json.loads(res.value)
    document_ids = res["document_ids"]
    entity_abstraction_mapping = res["entity_abstract_mapping"]

    cache_key = f"subtopic-cache-key-{'|'.join(categories)}-{'|'.join(entities)}-{len(document_ids)}"
    result = SystemConfig.get_or_create_dict_value(cache_key)
    if result:
        return jsonify(result)

    if categories:
        queryset = (
            DocumentEntityCategory.objects(
                news_analytics__in=document_ids,
                total_relevance_score__gte=0.01,
                category__nin=categories,
            )
            .limit(1000)
            .no_dereference()
        )
    else:
        queryset = (
            DocumentEntityCategory.objects(
                news_analytics__in=document_ids,
                total_relevance_score__gte=0.01,
                entity__in=entities,
            )
            .limit(1000)
            .no_dereference()
        )

    related_abstractions = dict()
    abstraction_documents = defaultdict(list)
    abstraction_entities = defaultdict(list)
    coverage_scores = defaultdict(list)
    entity_categories = defaultdict(list)
    for item in queryset:
        if categories:
            if (
                item.entity
                not in entity_abstraction_mapping[str(item.news_analytics.id)].keys()
            ):
                abstraction_documents[item.category].append(str(item.news_analytics.id))
                abstraction_entities[item.category].append(item.entity)
                coverage_scores[item.category].append(item.total_relevance_score)
                entity_categories[item.entity].append(item.category)
        else:
            abstraction_documents[item.category].append(str(item.news_analytics.id))
            abstraction_entities[item.category].append(item.entity)
            coverage_scores[item.category].append(item.total_relevance_score)
            entity_categories[item.entity].append(item.category)

    for category in abstraction_documents.keys():
        if len(set(abstraction_documents[category])) > 1:
            diversity_score = len(set(abstraction_entities[category])) / len(
                abstraction_entities[category]
            )
            related_abstractions[category] = {
                "abstraction": category,
                "documents": list(set(abstraction_documents[category])),
                "diversity_score": round(diversity_score, 3),
                "score": sum(coverage_scores[category]),
                "distinct_entities": list(set(abstraction_entities[category])),
            }

    # specificity score
    from app.models.dbpedia_category import DBPediaCategory

    specificity_queryset = DBPediaCategory.objects(
        name__in=list(related_abstractions.keys()),
        corpus_entity_count__gt=1,
        kg_entity_count__gt=1,
    )
    for dbpedia_category in specificity_queryset:
        record = related_abstractions[dbpedia_category.name]
        record["specificity_score"] = dbpedia_category.specificity_score or 0
        record["coverage_specificity"] = record["specificity_score"] + record.get(
            "score", 0
        )
        record["coverage_specificity_diversity"] = record.get(
            "coverage_specificity", 0
        ) + record.get("diversity_score", 0)
    return_abstractions = list(related_abstractions.values())

    # assign labels
    from app.models.dbpedia_entity_category import DBPediaEntityCategory

    subtopic_groups = list()
    for category in related_abstractions.keys():
        entities = related_abstractions[category]["distinct_entities"]
        found_group = False
        for record in subtopic_groups:
            group_entities = record["group_entities"]
            group_categories = record["group_categories"]
            if category in group_categories or set(entities).intersection(
                set(group_entities)
            ):
                record["group_categories"] += [category]
                record["group_entities"] += entities
                found_group = True
                break
        if not found_group:
            subtopic_groups.append(
                {
                    "group_entities": entities,
                    "group_categories": [category],
                }
            )

    for record in subtopic_groups:
        documents = set()
        for category in record["group_categories"]:
            documents = documents.union(related_abstractions[category]["documents"])

        record["group_documents"] = documents

    subtopic_groups.sort(
        key=lambda record: len(record["group_categories"])
        + len(record["group_entities"])
        + len(record["group_documents"]),
        reverse=True,
    )

    subtopic_tree = []
    for idx, record in enumerate(subtopic_groups):
        group = idx
        if idx < 4:
            subtopic_tree.append(
                {
                    "title": ", ".join(
                        {
                            item.split(":")[-1].replace("_", " ")
                            for item in list(record["group_entities"])[:3]
                        }
                    )
                    + "...",
                    "key": idx,
                    "children": [],
                }
            )

        elif idx == 4:
            subtopic_tree.append({"title": "Others", "key": idx, "children": []})
        else:  # idx > 4
            group = 4

        for category in record["group_categories"]:
            child = related_abstractions[category]
            child.update(
                {
                    "title": category,
                    "key": category,
                    "documents": related_abstractions[category]["documents"],
                }
            )
            subtopic_tree[group]["children"].append(child)
    return_abstractions.sort(
        key=lambda k: (k.get("coverage_specificity_diversity", 0)), reverse=True
    )
    for records in subtopic_tree:
        records["children"].sort(
            key=lambda k: (k.get("coverage_specificity_diversity", 0)), reverse=True
        )
    res = {
        "abstractions": return_abstractions,
        "document_ids": document_ids,
        "subtopic_tree": subtopic_tree,
    }

    cache_key = f"subtopic-cache-key-{'|'.join(categories)}-{'|'.join(entities)}-{len(document_ids)}"
    SystemConfig.update_dict_value(cache_key, res)

    return jsonify(res)


@services.route("/documents/<string:patterns>/<int:page>/<int:page_size>")
def get_documents_with_patterns(patterns=None, page=1, page_size=5):
    from app.models.news_analytics import NewsAnalytics

    terms = [item.strip() for item in patterns.split("|")]

    categories = [item for item in terms if item.find("Category:") > -1]
    entities = [item for item in terms if item.find("Category:") == -1]

    categories.sort()
    entities.sort()
    result = _pattern_documents(categories, entities)
    res = result["res"]
    entity_abstraction_mapping = result["entity_abstraction_mapping"]
    abstraction_mapping = result["abstraction_mapping"]

    document_ids = [item["_id"] for item in res]

    rendered_documents = []
    render_ids = document_ids[(page - 1) * page_size : page * page_size]
    for news_analytics in NewsAnalytics.objects(id__in=render_ids):
        record = json.loads(json.dumps(abstraction_mapping[str(news_analytics.id)]))
        mappings = entity_abstraction_mapping[str(news_analytics.id)]

        record["document"] = {
            "id": str(news_analytics.id),
            "publication_date": news_analytics.publication_date,
            "entity_html": news_analytics.render_spacy_entity_html(
                mappings, add_explaination=False
            ),
            "sentiment": news_analytics.sentiment_score,
        }
        rendered_documents.append(record)

    positive = NewsAnalytics.objects(id__in=document_ids, sentiment_score__gt=0).count()
    negative = NewsAnalytics.objects(id__in=document_ids, sentiment_score__lt=0).count()
    res = {
        "document_ids": document_ids,
        "bm25_result": {"docs": []},
        "bert_result": {"docs": []},
        "news_link_result": {"docs": {}},
        "abstract_search_result": {"docs": rendered_documents},
        "patterns": patterns,
        "sentiments": {
            "positive": positive,
            "neutral": len(document_ids) - positive - negative,
            "negative": negative,
        },
    }

    return jsonify(res)


@cache.memoize()
def _pattern_documents(categories, entities):
    if categories:
        pipeline = [
            {
                "$match": {
                    "category": {"$in": categories},
                    # "total_relevance_score": {"$gte": 0.01},
                },
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
                    "num_category": {"$eq": len(categories)},
                    "num_entity": {"$gte": len(categories)},
                }
            },
            {"$sort": {"total_relevance_score": -1}},
            # {"$limit": 100},
        ]
    else:
        pipeline = [
            {
                "$match": {
                    "entity": {"$in": entities},
                },
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
                    "num_entity": {"$gte": len(categories)},
                }
            },
        ]
    from app.models.document_entity_category import DocumentEntityCategory

    res = list(DocumentEntityCategory.objects.aggregate(pipeline))
    for item in res:
        item["_id"] = str(item["_id"])

    abstraction_mapping = defaultdict(lambda: defaultdict(list))
    entity_abstraction_mapping = defaultdict(dict)
    relevance_scores = dict()
    for item in res:
        relevance_scores[item["_id"]] = item.get("total_relevance_score", 0)
        for idx, category in enumerate(item["ordered_categories"]):
            abstraction_mapping[item["_id"]][category].append(
                item["ordered_entities"][idx]
            )
            entity_abstraction_mapping[str(item["_id"])][
                item["ordered_entities"][idx]
            ] = category

    from app.common.models import SystemConfig

    key = "pattern-documents-" + "|".join(categories) + "|".join(entities)

    SystemConfig.update_dict_value(
        key,
        {
            "document_ids": [item["_id"] for item in res],
            "entity_abstract_mapping": entity_abstraction_mapping,
        },
    )

    result = {
        "res": res,
        "entity_abstraction_mapping": dict(entity_abstraction_mapping),
        "abstraction_mapping": dict(abstraction_mapping),
    }
    return result


@services.route("/pattern_entities/<string:patterns>")
@cache.memoize()
def pattern_entities(patterns=None):
    print(patterns)
    abstractions = [item.strip() for item in patterns.split(",")]
    from app.models.document_entity_category import DocumentEntityCategory

    res = {}

    queryset = DocumentEntityCategory.objects(category__in=abstractions)

    entities = set()
    for item in queryset:
        res[item.category] = res.get(item.category, dict())
        res[item.category][item.entity] = ""
        entities.add(item.entity)

    from app.models.dbpedia_entity_alias import DBPediaEntityAlias

    queryset2 = DBPediaEntityAlias.objects(subject__in=list(entities)).only(
        "subject", "wikidata_id"
    )
    entity_wikidata_id_map = dict()
    for item in queryset2:
        entity_wikidata_id_map[item.subject] = item.wikidata_id

    for category, entities_dict in res.items():
        for entity in list(entities_dict.keys()):
            entities_dict[entity] = entity_wikidata_id_map.get(entity)

    result = {"pattern": abstractions, "entities": res}
    print(res)
    return jsonify(result)


@services.route("/entity_abstractions/<string:entities>")
@cache.memoize()
def entity_abstractions(entities):
    from app.models.dbpedia_entity_category import DBPediaEntityCategory

    entities = entities.split("|")
    categories = defaultdict(list)
    for item in DBPediaEntityCategory.objects(
        entity__in=entities, skip_in_analysis__ne=True
    ):
        categories[item.entity].append(item.category)
    print(f"{categories=} {entities}")
    return jsonify(categories)


@services.route("/pattern_relevance_survey", methods=["GET"])
def pattern_relevance_survey():
    """
    return least scored pattern as priority
    :return:
    """
    pipeline = [
        {
            "$group": {
                "_id": "$document_pattern",
                "count": {"$sum": 1},
            }
        },
        {"$sort": {"count": -1}},
    ]
    res = list(DocumentPatternEvaluation.objects.aggregate(pipeline))

    candidates = set(DocumentPattern.objects(trending=True).distinct("id"))

    if res and res[0]["count"] - res[-1]["count"] > 10:
        candidates = candidates.difference({item["_id"] for item in res[0:10]})

    names = DocumentPattern.objects(id__in=candidates).distinct("name")
    topics = dict()

    for name in names:
        tokens = name.split(",")

        if tokens[0].find("_companies_of_") > -1 or tokens[0].find("Countries_in") > -1:
            group = tokens[0]
            topic = tokens[1]
        else:
            group = tokens[1]
            topic = tokens[0]
        topics[topic] = topics.get(topic, [])
        topics[topic].append(group)

    response = {"topics": topics}

    return jsonify(response)


def _get_survey_questions(document_pattern):
    from app.models.document_entity_category import DocumentEntityCategory

    abstractions = [item.strip() for item in document_pattern.name.split(",")]
    abstractions.sort()

    if (
        abstractions[0].find("_companies_of_") > -1
        or abstractions[0].find("Countries_in") > -1
    ):
        group, topic = abstractions
    else:
        topic, group = abstractions

    print(group)
    entities = DocumentEntityCategory.objects(category=group).distinct("entity")
    print(entities)

    from app.evaluation.generate_survey_questions import generate_empty_survey_questions

    document_pattern_evaluation = generate_empty_survey_questions(document_pattern)

    documents = document_pattern_evaluation.documents
    import random

    random.shuffle(documents)

    docs = []
    for item in documents:
        item.entity_html = item.entity_html.replace(
            '<span style="font-size: 0.8em;', '<span style="display:none;'
        )
        item.entity_html = item.entity_html.replace(
            '<span class="neltooltiptext"', '<span style="display:none"'
        )
        docs.append({"id": str(item.id), "entity_html": item.entity_html})
    name = document_pattern.name
    res = {
        "documents": docs,
        "pattern_name": name,
        "topic": topic.split(":")[-1].replace("_", " "),
        "group": group.split(":")[-1].replace("_", " "),
        "display_names": [topic, group],
        "entities": entities,
    }
    return res


@cache.memoize()
def _get_connectivity_score_questions(abstractions):
    import random

    from app.models.document_entity_category import DocumentEntityCategory

    abstractions = [item.strip() for item in abstractions.split(",")]
    abstractions.sort()
    if (
        abstractions[0].find("_companies_of_") > -1
        or abstractions[0].find("Countries_in") > -1
    ):
        entity_abstraction = abstractions[0]
    else:
        entity_abstraction = abstractions[1]

    entities = DocumentEntityCategory.objects(category=entity_abstraction).distinct(
        "entity"
    )
    document_pattern = DocumentPattern.objects(name=",".join(abstractions)).first()

    document = random.choice(document_pattern.documents)
    queryset = DocumentEntityCategory.objects(
        news_analytics=document, entity__in=entities
    )
    categories = []
    for item in queryset:
        categories.append({"category": item.category, "entity": item.entity})
    print(entities)

    name = document_pattern.name
    res = {
        "document": document,
        "pattern_name": name,
        "display_names": [
            item.split(":")[-1].replace("_", " ") for item in name.split(",")
        ],
        "categories": categories,
    }
    return res


@services.route(
    "/abstraction_relevance_survey_questions/<string:abstractions>", methods=["GET"]
)
def abstraction_relevance_survey_questions(abstractions):
    res = _get_connectivity_score_questions(abstractions)
    res["evaluation_session"] = f"{uuid.uuid4()}"
    return jsonify(res)


@services.route("/answer_pattern_relevance_survey", methods=["POST"])
def answer_pattern_relevance_survey():
    from app.evaluation.generate_survey_questions import generate_empty_survey_questions

    data = request.json
    answers = data["answers"]
    pattern_name = data["pattern_name"]
    evaluation_session = data["evaluation_session"]
    document_pattern = DocumentPatternEvaluationQuestion.objects(
        name=pattern_name.strip()
    ).first()
    evaluation = DocumentPatternEvaluation.objects(
        document_pattern=document_pattern, evaluation_session=evaluation_session
    ).first()
    if not evaluation:
        evaluation = generate_empty_survey_questions(document_pattern)
        evaluation.evaluation_session = evaluation_session
    evaluation.scores = answers
    evaluation.save()
    res = {"remaining_questions": len(evaluation.documents) - len(evaluation.scores)}
    return jsonify(res)


@services.route("/answer_subtopic_relevance_survey", methods=["POST"])
def answer_subdomain_relevance_survey():
    data = request.json
    print(data)
    answers = data["answers"]
    evaluation_session = data["evaluation_session"]
    from app.models.perfomance_evaluation import SubdomainRecommendationSurveyResult

    record = SubdomainRecommendationSurveyResult.objects(
        evaluation_session=evaluation_session
    ).first()
    if not record:
        record = SubdomainRecommendationSurveyResult(
            evaluation_session=evaluation_session
        )
    record.ip_address = request.remote_addr
    record.answers = answers
    record.save()

    res = {"res": "ok"}
    return jsonify(res)
