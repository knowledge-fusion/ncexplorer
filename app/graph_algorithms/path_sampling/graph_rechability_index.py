import datetime
import json
import random
import sys
import traceback
from collections import defaultdict

import timeout_decorator
from mongoengine import Q
from pymongo.errors import DocumentTooLarge

from app.models.dbpedia_entity_linked_attribute import DBPediaEntityLinkedAttribute
from app.news_processor.calculate_document_entity_abstraction_score import (
    _connectivity_score_path_sum,
)


def _add_edge(G, from_node, to_node, total_length, target_node, order_in_path):
    G.add_edge(from_node, to_node)
    edge = G[from_node][to_node]
    edge["paths"] = edge.get("paths", [])
    record = {"length": total_length, "target": target_node, "order": order_in_path}
    if record not in edge["paths"]:
        edge["paths"].append(record)


@timeout_decorator.timeout(60)
def _build_reachable_tree(concept_entity, context_entities):

    import networkx as nx
    from networkx.readwrite import json_graph

    from app.models.dbpedia_entity_category import DBPediaEntityCategory

    G = nx.DiGraph()
    one_hop_neighbors = DBPediaEntityCategory.objects(category=concept_entity).distinct(
        "entity"
    )
    source_entities = set(one_hop_neighbors).intersection(context_entities)
    for entity in source_entities:
        one_hop_neighbors.remove(entity)
        context_entities.remove(entity)
    two_hop_neighbors = []
    two_hop_result = defaultdict(list)
    for item in DBPediaEntityLinkedAttribute.objects(subject__in=one_hop_neighbors):
        two_hop_result[item.subject].append(item.object)
        two_hop_neighbors.append(item.object)

    entities_to_expand = list(set(two_hop_neighbors).difference(set(context_entities)))

    from mongoengine import Q

    query1 = Q(subject__in=context_entities) & Q(object__in=entities_to_expand)
    query2 = Q(object__in=context_entities) & Q(subject__in=entities_to_expand)
    from app.models.dbpedia_entity_wikilink import DBPediaEntityWikilink

    queryset1 = DBPediaEntityWikilink.objects(query1)
    queryset2 = DBPediaEntityWikilink.objects(query2)

    reachable_two_hop_nodes = defaultdict(list)

    from itertools import chain

    for item in chain(queryset1, queryset2):
        if item.subject in context_entities:
            key = item.object
            val = item.subject
        elif item.object in context_entities:
            val = item.object
            key = item.subject
        else:
            raise ValueError(f"invalid result {item=}")
        if val not in reachable_two_hop_nodes[key]:
            reachable_two_hop_nodes[key].append(val)

    for one_hop_node, two_hop_nodes in two_hop_result.items():
        if one_hop_node in context_entities:
            _add_edge(
                G,
                from_node=concept_entity,
                to_node=one_hop_node,
                total_length=2,
                target_node=one_hop_node,
                order_in_path=1,
            )
            continue  # terminate
        for two_hop_node in (set(two_hop_neighbors)).intersection(
            set(
                context_entities
                + list(reachable_two_hop_nodes.keys())
                + list(source_entities)
            )
        ):
            if two_hop_node in context_entities:
                _add_edge(
                    G,
                    from_node=concept_entity,
                    to_node=one_hop_node,
                    total_length=3,
                    target_node=two_hop_node,
                    order_in_path=1,
                )
                _add_edge(
                    G,
                    from_node=one_hop_node,
                    to_node=two_hop_node,
                    total_length=3,
                    target_node=two_hop_node,
                    order_in_path=2,
                )
                continue

            if two_hop_node in reachable_two_hop_nodes.keys():
                for three_hop_node in reachable_two_hop_nodes[two_hop_node]:

                    _add_edge(
                        G,
                        to_node=three_hop_node,
                        from_node=two_hop_node,
                        total_length=4,
                        target_node=three_hop_node,
                        order_in_path=3,
                    )
                    _add_edge(
                        G,
                        to_node=two_hop_node,
                        from_node=one_hop_node,
                        total_length=4,
                        target_node=three_hop_node,
                        order_in_path=2,
                    )
                    _add_edge(
                        G,
                        to_node=one_hop_node,
                        from_node=concept_entity,
                        total_length=4,
                        target_node=three_hop_node,
                        order_in_path=1,
                    )

    graph_data = json_graph.node_link_data(G)
    return graph_data


def _generate_ground_truth_from_graph(directed_graph, concept_entity, context_entities):
    results = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    import numpy as np

    from app.models.dbpedia_entity_category import DBPediaEntityCategory

    concept_entities = DBPediaEntityCategory.objects(category=concept_entity).distinct(
        "entity"
    )
    one_hop_path_prefixes = []
    for one_hop_neighbor in directed_graph.neighbors(concept_entity):
        if one_hop_neighbor not in context_entities:

            one_hop_path_prefixes.append([concept_entity, one_hop_neighbor])

    two_hop_path_prefixes = []
    for one_hop_prefix in one_hop_path_prefixes:
        for two_hop_neighbor in directed_graph.neighbors(one_hop_prefix[-1]):
            if two_hop_neighbor in context_entities:
                results[one_hop_prefix[1]][two_hop_neighbor]["1"].append(
                    one_hop_prefix + [two_hop_neighbor]
                )
            else:
                two_hop_path_prefixes.append(one_hop_prefix + [two_hop_neighbor])

    for two_hop_prefix in two_hop_path_prefixes:
        candidate_neighbors = set()
        for neighbor in directed_graph.neighbors(two_hop_prefix[-1]):
            neighbor_paths = directed_graph[two_hop_prefix[-1]][neighbor]["paths"]
            paths_with_higher_order = [
                item for item in neighbor_paths if item["order"] == len(two_hop_prefix)
            ]
            if paths_with_higher_order:
                candidate_neighbors.add(neighbor)
        for three_hop_neighbor in candidate_neighbors:

            if three_hop_neighbor in context_entities:
                results[two_hop_prefix[1]][three_hop_neighbor]["2"].append(
                    two_hop_prefix + [three_hop_neighbor]
                )
            else:
                raise ValueError(
                    f"{two_hop_prefix + [three_hop_neighbor]} not in ground truth path {concept_entity} {context_entities}"
                )
    aggregated_result = defaultdict(dict)
    all_paths = []
    total_path_num = 0
    scores = []
    context_individual_scores = defaultdict(lambda: 0)
    for context_entity in context_entities:
        for connected_concept_entity in results.keys():
            paths_info = results[connected_concept_entity][context_entity]
            for paths in paths_info.values():
                for p in paths:
                    all_paths.append(" ".join(p))
            score = _connectivity_score_path_sum(
                {"1": len(paths_info["1"]), "2": len(paths_info["2"])}
            )

            if score:
                scores.append(score)
                context_individual_scores[context_entity] += score
            aggregated_result[connected_concept_entity][context_entity] = score
            total_path_num += (len(paths_info["1"])) + len(paths_info["2"])
    for connected_context_entity, score in context_individual_scores.items():
        print(
            f"{concept_entity}-{connected_context_entity} {score} average {score/len(concept_entities)}"
        )
    total = sum(scores) / len(context_entities)
    aggregated_result = json.loads(json.dumps(aggregated_result))
    assert len(set(all_paths)) == total_path_num
    return aggregated_result, total, total_path_num


def calculate_ground_truth_and_estimated_path_count(evaluation_object=None):
    import numpy as np
    from networkx.readwrite import json_graph

    from app.models.perfomance_evaluation import (
        ContextRelevanceScoreEvaluation,
        ContextRelevanceScoreEvaluationReachabilityIndex,
    )

    if not evaluation_object:
        queryset = ContextRelevanceScoreEvaluation.objects()
    else:
        queryset = [evaluation_object]

    for record in queryset:
        results = dict()

        reachable_graph = ContextRelevanceScoreEvaluationReachabilityIndex.objects(
            evaluation=record.id
        ).first()
        if False:
            reachable_graph.reachable_graph = _build_reachable_tree(
                record.category, record.context_entities + [record.entity]
            )
            reachable_graph.save()
        G = json_graph.node_link_graph(reachable_graph.reachable_graph)
        if not G.nodes:
            continue

        (
            aggregated_result,
            total_score,
            total_path_num,
        ) = _generate_ground_truth_from_graph(
            G, record.category, record.context_entities
        )

        normalized_total_score = 1 - 1 / (1 + total_score)
        print(
            f"calculate_ground_truth_and_estimated_path_count {record} {total_path_num=} {normalized_total_score=}"
        )
        """
        # targeted estimates
        estimates = []
        existing_paths = {}
        # record.targeted_sampling_estimates = targeted_random_walk_on_connected_tree(G, record)

        for length, paths in record.random_sampling_estimates.items():
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

        estimated_score = []
        running_errors = []
        for idx in range(len(estimates)):

            average = np.average(estimates[: idx + 1])
            estimated_score.append(average)
            normalized_average = 1 - 1 / (1 + average)
            error = (
                abs(normalized_average - normalized_total_score)
                / normalized_total_score
            )
            running_errors.append(error)
        record.random_sampling_errors = running_errors
        record.save()
        """
        estimates_no_index = []
        existing_paths = {}
        for length, paths in record.sampling_no_reachability_index_estimates.items():
            for item in paths:
                path = item["path"][1:]
                if not path:
                    estimates_no_index.append(0)
                    continue
                if " ".join(path) in existing_paths:
                    continue
                degree = item["degrees"]
                p = np.product(degree)
                existing_paths[" ".join(item["path"])] = p

                score = 0
                if len(path) == 2:
                    score = _connectivity_score_path_sum({"1": p, "2": 0})
                if len(path) == 3:
                    score = _connectivity_score_path_sum({"1": 0, "2": p})

                estimates_no_index.append(score)

        estimated_score_no_index = []
        running_errors_no_index = []
        for idx in range(len(estimates_no_index)):

            average = np.average(estimates_no_index[: idx + 1])
            estimated_score_no_index.append(average)
            normalized_average = 1 - 1 / (1 + average)
            error = (
                abs(normalized_average - normalized_total_score)
                / normalized_total_score
            )

            running_errors_no_index.append(error)
        record.sampling_no_reachability_index_errors = running_errors_no_index
        try:
            record.save()
        except DocumentTooLarge:
            record.reachable_graph = {}
            record.save()


def build_reachable_tree_task(skip=0):
    from app.models.perfomance_evaluation import (
        ContextRelevanceScoreEvaluation,
        ContextRelevanceScoreEvaluationReachabilityIndex,
    )

    version = 11
    query = Q(version__ne=version)
    record = ContextRelevanceScoreEvaluation.objects(query).skip(skip).first()
    while record:
        print(f"start {record}")
        try:
            reachable_graph = ContextRelevanceScoreEvaluationReachabilityIndex.objects(
                evaluation=record.id
            ).first()
            if not reachable_graph:
                reachable_graph = ContextRelevanceScoreEvaluationReachabilityIndex(
                    evaluation=record.id
                )
            if not reachable_graph.reachable_graph:
                start = datetime.datetime.utcnow()
                reachable_graph.reachable_graph = _build_reachable_tree(
                    record.category, record.context_entities
                )
                end = datetime.datetime.utcnow()
                reachable_graph.reachable_graph_time = (end - start).total_seconds()
                reachable_graph.save()

            if not reachable_graph.reachable_graph:
                record.version = version
                record.save()
                record = (
                    ContextRelevanceScoreEvaluation.objects(query).skip(skip).first()
                )
                continue

            from networkx.readwrite import json_graph

            G = json_graph.node_link_graph(reachable_graph.reachable_graph)

            if True:
                estimates = random_walk_on_connected_tree_no_reachability_index(
                    G.to_undirected(), record.category, record.context_entities
                )
                record.sampling_no_reachability_index_estimates = estimates
                record.save()

            if not record.random_sampling_estimates:
                start = datetime.datetime.utcnow()
                estimates = random_walk_on_connected_tree(
                    G, record.category, record.context_entities
                )
                end = datetime.datetime.utcnow()
                record.random_sampling_estimates = estimates
                record.random_sampling_time = (end - start).total_seconds()
                record.save()
            """
            if not record.collective_sampling_estimates:
                estimates = collective_random_walk_on_connected_tree(record)
                record.collective_sampling_estimates = estimates
                record.save()
                calculate_ground_truth_and_estimated_path_count(record)
            """
            print(f"done {record}")

        except Exception as e:
            traceback.print_exc(file=sys.stdout)

            print(f"{record} exception {e}")
        record.version = version
        record.save()
        record = ContextRelevanceScoreEvaluation.objects(query).skip(skip).first()


@timeout_decorator.timeout(30)
def targeted_random_walk_on_connected_tree(G, evaluation_object):

    estimates = {"2": [], "3": [], "4": []}
    for context_entity in evaluation_object.context_entities:
        count = 0
        while count < 10:
            count += 1
            terminate = False
            paths = [evaluation_object.category]
            degrees = []
            while not terminate and len(paths) < 4:
                neighbors = set()

                # only select neighbor at higher path order
                for neighbor in set(G.neighbors(paths[-1])):
                    neighbor_paths = G[paths[-1]][neighbor]["paths"]
                    paths_with_higher_order = [
                        item
                        for item in neighbor_paths
                        if item["order"] == len(paths)
                        and item["target"] == context_entity
                    ]
                    if paths_with_higher_order:
                        neighbors.add(neighbor)
                if not neighbors:
                    terminate = True
                    continue

                node = random.choice(list(neighbors))
                paths.append(node)
                terminate = node == context_entity

                degrees.append(len(neighbors))

            if degrees:
                estimates[str(len(paths))].append({"path": paths, "degrees": degrees})
    return estimates


@timeout_decorator.timeout(30)
def collective_random_walk_on_connected_tree(evaluation_object):
    from networkx.readwrite import json_graph

    G = json_graph.node_link_graph(evaluation_object.reachable_graph)
    estimates = dict()
    for context_entity in evaluation_object.context_entities:
        estimates[context_entity] = {"2": [], "3": [], "4": []}

    count = 0
    while count < 500 * len(evaluation_object.context_entities):
        count += 1
        terminate = False
        paths = [evaluation_object.concept_entity]
        degrees = []
        while not terminate and len(paths) < 4:
            neighbors = set()

            # only select neighbor at higher path order
            for neighbor in set(G.neighbors(paths[-1])):
                neighbor_paths = G[paths[-1]][neighbor]["paths"]
                paths_with_higher_order = [
                    item for item in neighbor_paths if item["order"] == len(paths)
                ]
                if paths_with_higher_order:
                    neighbors.add(neighbor)

            node = random.choice(list(neighbors))
            paths.append(node)
            terminate = node in evaluation_object.context_entities
            if not terminate:
                degrees.append(len(neighbors))
            else:
                degrees.append(1)

        if terminate:
            for context_entity in evaluation_object.context_entities:
                if context_entity == paths[-1]:
                    estimates[context_entity][str(len(paths))].append(degrees)
                else:
                    estimates[context_entity][str(len(paths))].append([0])

        else:
            raise ValueError(f"not terminated {paths}")
    return estimates


def random_walk_on_connected_tree(G, concept_entity, context_entities):

    estimates = {"2": [], "3": [], "4": []}
    count = 0
    while count < 50:
        terminate = False
        paths = [concept_entity]
        while not terminate and len(paths) < 4:
            neighbors = set()

            # only select neighbor at higher path order
            for neighbor in set(G.neighbors(paths[-1])):
                neighbor_paths = G[paths[-1]][neighbor]["paths"]
                paths_with_higher_order = [
                    item for item in neighbor_paths if item["order"] == len(paths)
                ]
                if paths_with_higher_order:
                    neighbors.add(neighbor)

            if not neighbors:
                raise ValueError(f"neighbors not found {paths}")

            neighbors = list(neighbors)
            random.shuffle(neighbors)
            node = random.choice(neighbors)
            paths.append(node)
            terminate = node in context_entities
        if terminate:
            count += 1
            degrees = []
            for idx, path_node in enumerate(paths[0:-1]):
                neighbors = set()
                path_info = {
                    "order": idx + 1,
                    "target": paths[-1],
                    "length": len(paths),
                }
                for neighbor in G.neighbors(path_node):
                    for edge_attr in G[path_node][neighbor]["paths"]:
                        if edge_attr == path_info:
                            neighbors.add(neighbor)
                            break

                degrees.append(len(neighbors))

            estimates[str(len(paths))].append({"path": paths, "degrees": degrees})
        else:
            raise ValueError(f"cannot terminate {paths}")
    return estimates


def random_walk_on_connected_tree_no_reachability_index(
    G, concept_entity, context_entities
):

    estimates = {"2": [], "3": [], "4": []}
    count = 0
    while count < 600:
        terminate = False
        paths = [concept_entity]
        while not terminate and len(paths) < 4:
            # only select neighbor at higher path order
            neighbors = G.neighbors(paths[-1])

            if not neighbors:
                raise ValueError(f"neighbors not found {paths}")

            neighbors = list(neighbors)
            random.shuffle(neighbors)
            node = random.choice(neighbors)
            paths.append(node)
            terminate = node in context_entities
        if terminate:
            count += 1
            degrees = []
            for idx, path_node in enumerate(paths[0:-1]):
                neighbors = set()
                path_info = {
                    "order": idx + 1,
                    "target": paths[-1],
                    "length": len(paths),
                }
                for neighbor in G.neighbors(path_node):
                    for edge_attr in G[path_node][neighbor]["paths"]:
                        if edge_attr == path_info:
                            neighbors.add(neighbor)
                            break

                degrees.append(len(neighbors))

            estimates[str(len(paths))].append({"path": paths, "degrees": degrees})
        else:
            estimates[str(len(paths))].append({"path": [], "degrees": [0, 0, 0, 0]})
    return estimates
