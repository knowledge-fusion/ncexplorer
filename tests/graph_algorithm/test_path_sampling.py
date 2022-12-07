import datetime


def test_sample_path_until_n_success():
    from app.graph_algorithms.path_sampling import sample_path_until_n_success

    sample_path_until_n_success()


def test_calculate_estimated_paths_count():
    from app.graph_algorithms.path_sampling import calculate_estimated_paths_count

    calculate_estimated_paths_count()


def test_print_estimate_correlation():
    from app.graph_algorithms.path_sampling import print_estimate_correlation

    print_estimate_correlation()


def test_build_reachable_tree_task():
    from app.graph_algorithms.path_sampling.graph_rechability_index import (
        build_reachable_tree_task,
    )

    build_reachable_tree_task()


def test_random_walk_on_connected_tree():
    from app.graph_algorithms.path_sampling.graph_rechability_index import (
        calculate_ground_truth_and_estimated_path_count,
    )
    from app.models.perfomance_evaluation import ContextRelevanceScoreEvaluation

    queryset = ContextRelevanceScoreEvaluation.objects(
        category__in=[
            "Category:Port_cities_and_towns_of_the_Atlantic_Ocean",
        ],
        incorrect_category="Category:People_convicted_of_murder_by_California",
    )
    start = datetime.datetime.utcnow()
    # estimates = collective_random_walk_on_connected_tree(record)
    for record in queryset:
        print(record)
        calculate_ground_truth_and_estimated_path_count(record)
    end = datetime.datetime.utcnow()
