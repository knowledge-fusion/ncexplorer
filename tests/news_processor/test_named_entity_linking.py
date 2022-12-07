def test_named_entity_linking(test_news_url):
    from app.news_processor.named_entity_linking import _named_entity_linking

    url = "https://www.bloomberg.com/news/articles/2022-09-15/us-railroads-unions-agree-on-a-tentative-pact-government-says"

    _named_entity_linking(url.strip())
