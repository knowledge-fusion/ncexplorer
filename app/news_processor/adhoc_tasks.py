import datetime


def task_data_cleaning():
    from app.common.settings import news_content_blacklist, news_title_blacklist
    from app.models.news import News
    from app.models.news_analytics import NewsAnalytics

    for keyword in news_title_blacklist:
        flt = {"title__icontains": keyword}
        News.objects(**flt).delete()
        for analytics in NewsAnalytics.objects(**flt):
            analytics.delete()
    for keyword in news_content_blacklist:
        News.objects(content__icontains=keyword).delete()
        for analytics in NewsAnalytics.objects(text__icontains=keyword):
            analytics.delete()


def task_run_pipeline(skip):
    from app.news_processor.calculate_document_entity_abstraction_score import (
        task_calculate_document_entity_abstraction_score,
    )
    from app.news_processor.calculate_document_entity_score import (
        task_batch_calculate_entity_tfidf_score,
    )
    from app.news_processor.calculate_document_sentiment_score import (
        task_batch_calculate_document_sentiment_score,
    )
    from app.news_processor.extract_document_entity_abstraction import (
        task_extract_document_abstraction,
    )
    from app.news_processor.named_entity_linking import task_named_entity_linking

    start = datetime.datetime.utcnow()
    task_named_entity_linking(skip)
    a1 = datetime.datetime.utcnow() - start
    task_batch_calculate_document_sentiment_score()
    print(f"task_named_entity_linking {a1}")
    task_extract_document_abstraction(skip)
    a2 = datetime.datetime.utcnow() - start
    print(f"task_extract_document_abstraction {a2}")
    task_batch_calculate_entity_tfidf_score(skip)
    print(f"task_extract_document_abstraction")

    a3 = datetime.datetime.utcnow() - start
    task_calculate_document_entity_abstraction_score(skip)
    a4 = datetime.datetime.utcnow() - start
    print(f"task_calculate_document_entity_abstraction_score {a3}")

    # task_calculate_document_entity_abstraction_expansion_score(skip)
    # task_calculate_document_entity_cooccurrence_count(skip)
    # task_calculate_document_abstraction_cooccurrence_count(skip)
    # task_register_document_seed_patterns(skip)

    # task_document_pattern_generation(skip)
    # task_calculate_document_pattern_score_batch(skip)
    return a1, a2, a3, a4
