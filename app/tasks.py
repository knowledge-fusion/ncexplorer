#!/usr/bin/env python
# -*- coding: utf-8 -*-
import datetime

from celery import chord
from celery import group
from flask import current_app

from app.application import celery


# pylint: disable=invalid-name,unused-argument
from app.finance_news.models import FinanceNews
from app.watson.models import WatsonAnalytics

logger = celery.log.get_default_logger()


@celery.task(bind=True, name="tasks.test")
def test(self):
    logger.info("celery_beat_test")
    return True


###
# watson
###


@celery.task(bind=True, name="tasks.watson_analyze_webpage", ignore_result=False)
def watson_analyze_webpage(self, url, html):
    from app.watson.analyze import analyze

    result = None
    try:
        result = analyze(url=url, html=html)
    except Exception as exc:
        logger.exception(exc)
        result = exc.message
    return result


@celery.task(bind=True, name="tasks.watson_analytics")
def watson_analytics(self):
    existing_urls = WatsonAnalytics.objects.distinct('url')
    tasks = []
    for item in FinanceNews.objects(url__nin=existing_urls).only('url', 'html').limit(30):
        tasks.append(watson_analyze_webpage.s(item.url, item.html))
    return group(tasks)()


###
# hooks
###

@celery.task
def error_handler(uuid):
    from celery.result import AsyncResult
    result = AsyncResult(uuid)
    exc = result.get(propagate=False)
    logger.error('Task {0} raised exception: {1!r}\n{2!r}'.format(
        uuid, exc, result.traceback))
