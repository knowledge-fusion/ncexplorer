import datetime
import json

from flask import current_app
from mongoengine import Q
from pymongo.errors import DocumentTooLarge
from timeout_decorator import timeout_decorator

from app.utils import chunks

USE_CACHE = False


def _document_entity_abstraction_score(news_analytics):
    print(news_analytics.url)

    entity_abstractions = news_analytics.entity_abstractions

    noun_entity_categories = []
    noun_entities = []
    for entity, categories in entity_abstractions.items():
        if categories[0].category.find("Category:") > -1:
            noun_entity_categories += categories
            noun_entities.append(entity)

    for item in noun_entity_categories:
        if item.concept_relevance_score:
            continue

        try:
            print(f"{item.category} <> {noun_entities} ")

            connectivity_score, duration = calculate_concept_relevance_scores(
                item.category, noun_entities
            )
            item.concept_relevance_score = connectivity_score
            item.calculation_time = duration
            item.total_relevance_score = (
                item.concept_relevance_score * item.entity_relevance_score
            )
            print(f"{item} {item.concept_relevance_score=} {item.calculation_time}")
            item.save()
        except DocumentTooLarge:
            item.concept_relevance_score = -1
            item.kg_paths = dict()
            item.save()
        except Exception as e:
            current_app.logger.error(e, exc_info=True)


DELIMITER = "|--|"


def _calculate_path_connectivity_scores(
    item, source_entity, source_neighbors, target_entity, target_neighbors
):
    item.one_hop_path_count = 0
    if target_entity in source_neighbors:
        item.one_hop_path_count = 1
    if source_entity in target_neighbors:
        item.one_hop_path_count = 1
    two_hop_neighbors = set(target_neighbors.keys()).intersection(
        set(source_neighbors.keys())
    )
    two_hop_paths = dict()
    for key in two_hop_neighbors:
        sanitized_key = key  # re.sub("\W+", "", "%s" % key)
        if sanitized_key.startswith("$"):
            sanitized_key = sanitized_key.replace("$", "DOLLAR_")

        two_hop_paths[sanitized_key] = {
            "source_paths": source_neighbors[key],
            "target_paths": target_neighbors[key],
        }

    item.two_hop_paths = two_hop_paths
    item.two_hop_path_count = len(two_hop_neighbors)
    item.version = 2
    try:
        item.save()
    except DocumentTooLarge as e:
        two_hop_paths = {key: [] for key, value in item.two_hop_paths.items()}

        item.two_hop_paths = two_hop_paths
        item.save()
    return item


@timeout_decorator.timeout(600)
def calculate_three_hop_concept_relevance_scores(
    concept, primary_linked_context_entity, context_entities, sample_count=None
):
    import random

    from app.models.dbpedia_entity_category import DBPediaEntityCategory
    from app.models.dbpedia_entity_wikilink import DBPediaEntityWikilink

    concept_entities = DBPediaEntityCategory.objects(
        category=concept, entity__nin=context_entities
    ).distinct("entity")

    if not concept_entities:
        return []
    if primary_linked_context_entity in context_entities:
        context_entities.remove(primary_linked_context_entity)

    if len(concept_entities) > 10:
        concept_entities = random.sample(concept_entities, k=10)

    from collections import defaultdict

    paths_result = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    entity_neighbors = defaultdict(list)
    one_hop_neighbors = []
    query = Q(subject__in=concept_entities) | Q(object__in=concept_entities)
    for item in DBPediaEntityWikilink.objects(query).limit(sample_count):
        concept_entity, neighbor = (
            (item.subject, item.object)
            if item.subject in concept_entities
            else (item.object, item.subject)
        )

        if neighbor in context_entities:
            paths_result[concept_entity][neighbor]["1"].append(
                [concept_entity, neighbor]
            )
        else:
            entity_neighbors[neighbor].append(concept_entity)
            one_hop_neighbors.append(neighbor)

    one_hop_neighbors = list(set(one_hop_neighbors))
    import itertools

    two_hop_candidates = []
    print(f"one_hop_neighbors length {len(one_hop_neighbors)}")
    for one_hop_neighbors_subset in chunks(one_hop_neighbors, 100):
        print(one_hop_neighbors_subset[-1])
        query = Q(subject__in=one_hop_neighbors_subset) | Q(
            object__in=one_hop_neighbors_subset
        )
        for item in DBPediaEntityWikilink.objects(query).limit(sample_count):

            last_node, second_node = (
                (item.subject, item.object)
                if item.object in one_hop_neighbors_subset
                else (item.object, item.subject)
            )
            if last_node in context_entities:
                for first_node in entity_neighbors[second_node]:
                    paths_result[first_node][last_node]["2"].append(
                        [first_node, second_node, last_node]
                    )
            else:
                two_hop_candidates.append(last_node)
                entity_neighbors[last_node].append(second_node)
    query = Q(subject__in=context_entities) | Q(object__in=context_entities)
    for item in DBPediaEntityWikilink.objects(query):
        last_node, third_node = (
            (item.subject, item.object)
            if item.subject in context_entities
            else (item.object, item.subject)
        )
        if third_node in two_hop_candidates:
            for second_node in entity_neighbors[third_node]:
                for first_node in entity_neighbors[second_node]:
                    paths_result[first_node][last_node]["3"].append(
                        [first_node, second_node, third_node, last_node]
                    )

    results = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

    for first_node, last_node in list(
        itertools.product(concept_entities, context_entities)
    ):
        result = paths_result[first_node][last_node]
        results[first_node][last_node] = {
            "1": len(result["1"]),
            "2": len(result["2"]),
            "3": len(result["3"]),
        }

    results = json.loads(json.dumps(results))
    return results


def calculate_concept_relevance_scores(concept, context_entities):
    import numpy as np
    from networkx.readwrite import json_graph

    from app.graph_algorithms.path_sampling.graph_rechability_index import (
        _build_reachable_tree,
        random_walk_on_connected_tree,
    )

    # swap this for the reachability index in your KG
    reachable_graph = _build_reachable_tree(concept, context_entities)

    G = json_graph.node_link_graph(reachable_graph)

    if not G.nodes:
        return 0, 0

    start = datetime.datetime.utcnow()
    random_walk_estimates = random_walk_on_connected_tree(
        G, concept_entity=concept, context_entities=context_entities
    )

    estimates = []
    existing_paths = {}

    for length, paths in random_walk_estimates.items():
        for item in paths:
            if " ".join(item["path"]) in existing_paths:
                continue

            path = item["path"][1:]
            degree = item["degrees"]
            p = np.product(degree)
            existing_paths[" ".join(item["path"])] = p
            score = 0
            if len(path) == 2:
                score = _connectivity_score_path_sum({"1": p, "2": 0})
            if len(path) == 3:
                score = _connectivity_score_path_sum({"1": 0, "2": p})

            estimates.append(score)
    average = np.average(estimates)
    normalized_average = 1 - 1 / (1 + average)

    end = datetime.datetime.utcnow()
    duration = (end - start).total_seconds()
    return normalized_average, duration


def task_calculate_document_entity_abstraction_score(skip=0):
    from app.models.news_analytics import NewsAnalytics, NewsAnalyticsProcessingState

    query = Q(
        processing_state=NewsAnalyticsProcessingState.DOCUMENT_ENTITY_SCORE_CALCULATED.value,
    )

    item = NewsAnalytics.objects(query).skip(skip).first()
    while item:
        print(
            f"start task_calculate_document_entity_abstraction_score {skip} {item.url}"
        )
        _document_entity_abstraction_score(item)
        item.processing_state = (
            NewsAnalyticsProcessingState.DOCUMENT_ENTITY_ABSTRACTION_SCORE_CALCULATED.value
        )
        item.save()

        item = NewsAnalytics.objects(query).skip(skip).first()


def _connectivity_score_path_sum(path_length_map):
    total = 0
    beta = 0.5
    for length, count in path_length_map.items():
        total += pow(beta, int(length)) * count
    return total
