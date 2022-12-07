import os

from app.news_importer.newsriver_importer import NewsRiverImporter


def test_news_river_fetch(app):
    token = os.getenv("NEWS_RIVER%s" % 0)
    importer = NewsRiverImporter(token=token)
    res = importer.fetch_documents()
    res
