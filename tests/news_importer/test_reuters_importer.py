def test_processing_documents():
    from app.models.news import News, NewsProcessingState
    from app.news_importer.reuters_importer import ReutersImporter

    importer = ReutersImporter()
    importer.fetch_documents()
    news = News.objects(
        source=importer.source, processing_state=NewsProcessingState.EMPTY.value
    ).first()
    importer.clean_document(news.url)


def test_extract_snippet():
    from app.news_importer.reuters_importer import ReutersImporter

    importer = ReutersImporter()
    from app.models.news import News

    for item in News.objects(source="reuters", processing_state="imported"):
        importer.extract_snippet(item)
