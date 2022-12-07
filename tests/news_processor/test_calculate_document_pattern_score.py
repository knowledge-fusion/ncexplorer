def test_calculate_document_pattern_score():
    from app.models.document_pattern import DocumentPattern
    from app.news_processor.calculate_document_pattern_score import (
        _calculate_document_pattern_relevance_score,
    )

    queryset = list(
        DocumentPattern.objects(
            name="Category:Member_states_of_the_United_Nations,Category:Russia"
        )
    )
    for item in queryset:
        _calculate_document_pattern_relevance_score(item)


def test_export_pattern_to_txt_file():
    from app.news_processor.calculate_document_pattern_score import (
        export_pattern_to_txt_file,
    )

    export_pattern_to_txt_file()


def test_task_refresh_pattern_and_subtopics():
    from app.models.document_pattern import DocumentPattern
    from app.news_processor.calculate_document_pattern_score import (
        task_refresh_pattern_and_subtopics,
    )

    document_patterns = DocumentPattern.objects(name="Category:Russia")

    task_refresh_pattern_and_subtopics(list(document_patterns))
