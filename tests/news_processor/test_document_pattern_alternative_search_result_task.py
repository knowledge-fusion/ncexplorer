def test_task_calculate_document_pattern_alternative_search_result_batch():
    from app.news_processor.calculate_document_pattern_alternative_result import (
        task_calculate_document_pattern_alternative_search_result_batch,
    )

    task_calculate_document_pattern_alternative_search_result_batch()


def test_calculate_pattern_alternative_search_result_statistics():
    from app.news_processor.calculate_document_pattern_alternative_result import (
        calculate_pattern_alternative_search_result_statistics,
    )

    calculate_pattern_alternative_search_result_statistics()


def test_calculate_category_average_semantic_distance():
    from app.models.document_pattern import DocumentPattern
    from app.news_processor.calculate_document_pattern_alternative_result import (
        calculate_category_average_semantic_distance,
    )

    document_pattern = DocumentPattern.objects(
        category_average_semantic_distance=None, category_count=2
    ).first()
    calculate_category_average_semantic_distance(document_pattern)


def test_label_meaningful_patterns():
    from app.news_processor.calculate_document_pattern_alternative_result import (
        label_meaningful_patterns,
    )

    label_meaningful_patterns()
