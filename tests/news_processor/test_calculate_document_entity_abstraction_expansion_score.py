def test_document_entity_abstraction_expansion_score():
    from app.models.news_analytics import NewsAnalytics
    from app.news_processor.calculate_document_entity_abstraction_expansion_score import (
        _document_entity_abstraction_expansion_score,
    )

    url = "https://www.nytimes.com/2022/04/25/opinion/editorials/twitter-elon-musk.html"
    news_analytics = NewsAnalytics.objects(url=url.strip()).first()
    _document_entity_abstraction_expansion_score(news_analytics)
