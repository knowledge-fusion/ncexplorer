def test_calculate_analytics_document_pattern_score():
    url = " https://seekingalpha.com/news/3349353-amd-ceo-appears-cnbc-reveals-crypto-mining-impact "
    from app.models.document_pattern import DocumentPattern
    from app.models.news_analytics import NewsAnalytics, NewsAnalyticsProcessingState
    from app.news_processor.calculate_document_entity_abstraction_score import (
        _document_entity_abstraction_score,
    )
    from app.news_processor.calculate_document_pattern_score import (
        _calculate_document_pattern_relevance_score,
    )

    news_analytics = NewsAnalytics.objects(url=url.strip()).first()
    for item in DocumentPattern.objects(
        documents__in=[news_analytics.id],
        kg_connectivity=None,
    ):
        for news in item.documents:
            if (
                news.processing_state
                == NewsAnalyticsProcessingState.DOCUMENT_ENTITY_SCORE_CALCULATED.value
            ):
                _document_entity_abstraction_score(news)
                news.processing_state = (
                    NewsAnalyticsProcessingState.DOCUMENT_ENTITY_ABSTRACTION_SCORE_CALCULATED.value
                )
                news.save()
        print(item)
        _calculate_document_pattern_relevance_score(item)


def test_task_expand_document_pattern_subtopics():
    from app.news_processor.calculate_document_pattern_score import (
        task_calculate_document_pattern_subtopics,
    )

    task_calculate_document_pattern_subtopics()


def test_refresh_pattern_documents():
    from app.models.document_pattern import DocumentPattern
    from app.news_processor.calculate_document_pattern_score import (
        _calculate_document_pattern_relevance_score,
    )

    record = DocumentPattern.objects(
        name="Category:Mergers_and_acquisitions,Category:Nasdaq,_Inc.,Category:Software_companies_of_the_United_States"
    ).first()
    _calculate_document_pattern_relevance_score(record)


def test_calculate_document_pattern_score():
    from app.models.document_pattern import DocumentPattern

    record = DocumentPattern.objects(
        name="Category:Geography_of_North_Slope_Borough,_Alaska"
    ).first()
    from app.news_processor.calculate_document_pattern_score import (
        _calculate_document_pattern_relevance_score,
    )

    _calculate_document_pattern_relevance_score(record)


def test_expand_subtopics():
    from app.models.document_pattern import DocumentPattern
    from app.news_processor.calculate_document_pattern_score import (
        _calculate_document_pattern_subtopics,
    )

    categories = ["Category:Eastern_European_countries,Category:Violent_conflict"]
    for item in DocumentPattern.objects(name__in=categories):
        _calculate_document_pattern_subtopics(item)


def test_calculate_document_pattern_diversity_score():
    from app.models.document_pattern import (
        DocumentPattern,
        DocumentPatternProcessingState,
    )
    from app.news_processor.calculate_document_pattern_score import (
        _calculate_document_pattern_diversity_score,
    )

    record = (
        DocumentPattern.objects(
            processing_state=DocumentPatternProcessingState.DOCUMENTS_UPDATED.value,
            document_count__gt=1,
        )
        .order_by("-document_count")
        .no_dereference()
        .first()
    )
    _calculate_document_pattern_diversity_score(record)
    from app.news_processor.calculate_document_pattern_score import (
        task_calculate_document_pattern_diversity_score,
    )

    task_calculate_document_pattern_diversity_score(0)
