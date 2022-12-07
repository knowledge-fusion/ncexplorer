from app.news_importer.mediastack_importer import MediaStackImporter


def test_media_stack_fetch(app):
    importer = MediaStackImporter()
    res = importer.fetch_documents()


def test_clean_media_stack_document(app):
    importer = MediaStackImporter()
    from app.models.news import News

    for news in News.objects(
        processing_state="cleaned", source=importer.source, snippet=None
    ):
        importer.clean_document(news.url)
