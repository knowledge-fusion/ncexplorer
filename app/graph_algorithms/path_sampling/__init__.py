import datetime
from functools import reduce

from mongoengine import Q
from pymongo.errors import DocumentTooLarge

from app.extenstions import cache


def get_kg_paths(concept_entity, instance_entity, path_length):
    """

    :param source:
    :param target:
    :param path_length:
    :return: value
    """
    from app.models.dbpedia_entity_category import DBPediaEntityCategory
    from app.news_processor.calculate_document_entity_abstraction_score import (
        get_entity_sets_paths,
    )

    concept_entities = DBPediaEntityCategory.objects(
        category=concept_entity, entity__nin=[instance_entity]
    ).distinct("entity")

    if not concept_entities:
        return {}

    paths = get_entity_sets_paths(
        abstraction_entities=concept_entities,
        context_entities=[instance_entity],
    )

    # count by length


def get_kg_paths_sampling(
    concept_entity,
    instance_entities,
    path_length,
    along_reachable_path=True,
    ground_truth_paths=[],
):
    """

    :param source:
    :param target:
    :param path_length:
    :return: value, probability
    """
    import random
    from operator import mul

    from app.models.dbpedia_entity_category import DBPediaEntityCategory
    from app.news_processor.calculate_document_entity_abstraction_score import (
        _get_entity_neighbor,
    )

    concept_entities = DBPediaEntityCategory.objects(
        category=concept_entity, entity__nin=instance_entities
    ).distinct("entity")

    # candidate_entities = concept_entities
    paths = [concept_entity]
    probabilities = []
    reachable_candidates = []
    while len(paths) <= path_length:
        if along_reachable_path:

            reachable_candidates = set()
            for candidate in ground_truth_paths:
                if candidate[: len(paths)] == paths:
                    reachable_candidates.add(candidate[len(paths)])

        if reachable_candidates:
            entity = random.choice(list(reachable_candidates))
            probabilities.append(1 / len(reachable_candidates))
        else:
            # entity = random.choice(candidate_entities)
            for answer in ground_truth_paths:
                if answer[1 : 1 + len(paths)] == paths:
                    print(f"candidate path {answer}")
            raise ValueError(
                f"no connected entity found, {concept_entity} {instance_entities} {paths}"
            )
        # neighbors = _get_entity_neighbor(entity)
        # candidate_entities = list(neighbors.keys())
        paths.append(entity)

    probability = reduce(mul, probabilities, 1)
    if paths[-1] in instance_entities:
        return 1, probability, paths
    else:
        return 0, probability, paths


def sample_path_until_n_success():
    from app.models.perfomance_evaluation import PathCountSamplingEvaluation

    # query = Q(error_from_ground_truth__gte=0.5, sampled_paths=None)
    query = Q(reachable_graph_probabilities__90__exists=False)
    record = PathCountSamplingEvaluation.objects(query).first()
    while record:
        print(record)
        ground_truth_paths = record.ground_truth_paths
        # print(ground_truth_paths)
        record.reachable_graph_probabilities = []
        while len(record.reachable_graph_probabilities) < 100:

            res = get_kg_paths_sampling(
                concept_entity=record.concept_entity,
                instance_entities=[record.instance_entity],
                path_length=record.path_length,
                along_reachable_path=True,
                ground_truth_paths=ground_truth_paths,
            )
            total_success = 0
            success, probability, paths = res
            print(probability, paths)
            if success:
                total_success += 1
                record.reachable_graph_probabilities += [probability]
            else:
                record.reachable_graph_probabilities += [-probability]
            record.save()
        record = PathCountSamplingEvaluation.objects(query).first()


def calculate_estimated_paths_count():
    from app.models.perfomance_evaluation import PathCountSamplingEvaluation

    # for record in PathCountSamplingEvaluation.objects():
    #     if sum(record.reachable_graph_probabilities) < 0:
    #         record.reachable_graph_probabilities = None
    #         record.save()
    for record in PathCountSamplingEvaluation.objects():
        estimates = []
        running_average = []
        for probability in record.reachable_graph_probabilities:
            if probability > 0:
                estimates.append(int(1 / probability))
            else:
                estimates.append(0)
            mean = sum(estimates) / len(estimates)
            error = round(
                abs(mean - record.ground_truth_paths_count)
                / record.ground_truth_paths_count,
                2,
            )
            running_average.append(error)
        record.running_errors = running_average
        record.sample_count = len(estimates)
        record.save()


def print_estimate_correlation():
    import numpy as np

    ground_truth_values = []
    estimates = []
    from app.models.perfomance_evaluation import PathCountSamplingEvaluation

    for item in PathCountSamplingEvaluation.objects(paths_count_estimates__ne=None):
        ground_truth_values.append(item.ground_truth_paths_count)
        estimates.append(item.paths_count_estimates[-1])
    corr1 = np.corrcoef(ground_truth_values, estimates)
    print(
        f"ground truth <> estimates {corr1} {len(ground_truth_values)} {len(estimates)}"
    )
