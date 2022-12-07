import os
from time import sleep

from flask import current_app

from app.application import celery
from app.models.news import News, NewsProcessingState


@celery.task
def task_process_reuters_news():
    from app.news_importer.reuters_importer import ReutersImporter

    importer = ReutersImporter()
    importer.clean_documents()


@celery.task
def task_process_seekingalpha_news():
    from app.news_importer.seeking_alpha_importer import SeekingAlphaImporter

    importer = SeekingAlphaImporter()
    News.objects(source=importer.source, url__icontains="filing").update(
        set__processing_state=NewsProcessingState.SKIPPED.value
    )
    News.objects(source=importer.source, html=None).update(
        set__processing_state=NewsProcessingState.EMPTY.value
    )

    importer.clean_documents()


@celery.task
def task_fetch_nyt_news():
    key = current_app.config["NYT_KEY"]
    from app.news_importer.new_york_times_importer import NewYorkTimesImporter

    importer = NewYorkTimesImporter(key=key)
    res = importer.fetch_documents()
    return res


@celery.task
def fetch_newsriver_update(self):
    has_more = True
    for i in range(0, 6):
        if not has_more:
            break
        num_query = 0
        while num_query <= 100:
            from app.news_importer.newsriver_importer import NewsRiverImporter

            NewsRiverImporter(token=os.getenv("NEWS_RIVER%s" % i)).fetch_documents()
            num_query += 1
            sleep(1)
    return True
