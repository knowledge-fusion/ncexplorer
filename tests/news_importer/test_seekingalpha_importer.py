def test_processing_documents():
    from app.models.news import News, NewsProcessingState
    from app.news_importer.seeking_alpha_importer import SeekingAlphaImporter

    importer = SeekingAlphaImporter()
    news = News.objects(
        source=importer.source, processing_state=NewsProcessingState.EMPTY.value
    ).first()
    importer.clean_document(news.url)
