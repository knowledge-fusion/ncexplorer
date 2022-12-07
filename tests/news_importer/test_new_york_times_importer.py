from app.news_importer.new_york_times_importer import NewYorkTimesImporter


def test_new_york_times_importer(app):
    key = app.config["NYT_KEY"]
    importer = NewYorkTimesImporter(key=key)
    # res = importer.fetch_documents()
    res = importer.fetch_latest()
    res


def test_clearn_newyork_times_document(app):
    key = app.config["NYT_KEY"]
    importer = NewYorkTimesImporter(key=key)
    from app.models.news import News

    for news in News.objects(
        processing_state="cleaned", source=importer.source, snippet=None
    ):
        importer.clean_document(news.url)
