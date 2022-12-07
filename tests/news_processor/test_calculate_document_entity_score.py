def test_calculate_document_entity_score():
    from app.news_processor.calculate_document_entity_score import (
        _calculate_document_entity_score,
    )

    url = "  20150309-142350000-nL5N0WB2IS-1-2  "
    from app.models.news_analytics import NewsAnalytics

    new_analytics = NewsAnalytics.objects(url=url.strip()).first()

    _calculate_document_entity_score(new_analytics)


def test_generate_corpus_tf_idf_vocabulary():
    from app.news_processor.calculate_corpus_term_weight import (
        generate_corpus_tf_idf_vocabulary,
    )

    generate_corpus_tf_idf_vocabulary()


def test_task_batch_calculate_entity_tfidf_score():
    from app.news_processor.calculate_document_entity_score import (
        task_batch_calculate_entity_tfidf_score,
    )

    task_batch_calculate_entity_tfidf_score()
