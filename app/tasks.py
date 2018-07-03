#!/usr/bin/env python
# -*- coding: utf-8 -*-
import datetime
import os
from time import sleep

from celery import chord
from celery import group
from flask import current_app

from app.application import celery

# pylint: disable=invalid-name,unused-argument
from app.finance_news.models import FinanceNews, Stock
from app.stock.fetch import fetch_daily_stock_data
from app.stock.models import StockDailyTimeSeries
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
def watson_analyze_webpage(self, username, password, url, html):
    from app.watson.analyze import analyze

    result = None
    try:
        print username
        result = analyze(username, password, url=url, html=html)
    except Exception as exc:
        logger.exception(exc)
        result = exc.message
    return result


@celery.task(bind=True, name="tasks.watson_analytics")
def watson_analytics(self):
    existing_urls = WatsonAnalytics.objects.distinct('url')
    credentials = []
    for i in xrange(3, 11):
        credentials.append((os.getenv('WATSON_USERNAME%s' % i), os.getenv('WATSON_PASSWORD%s' % i)))
    tasks = []
    queryset = FinanceNews.objects(url__nin=existing_urls, html__ne=None).only('url', 'html').limit(
        30 * len(
        credentials))
    for idx, item in enumerate(queryset):
        username, password = credentials[idx % len(credentials)]
        tasks.append(watson_analyze_webpage.s(username, password, item.url, item.html))
    return group(tasks)()


@celery.task(bind=True, name='tasks.stock_daily_timeseries_data_fetch_symbol')
def stock_daily_timeseries_data_fetch_symbol(self, symbol):
    return fetch_daily_stock_data(symbol, 'full')


@celery.task(bind=True, name="tasks.stock_daily_timeseries_data")
def stock_daily_timeseries_data(self):
    symbols = StockDailyTimeSeries.objects.distinct('symbol')
    queryset = Stock.objects(symbol__nin=symbols).only('symbol')
    tasks = []
    for item in queryset:
        tasks.append(stock_daily_timeseries_data_fetch_symbol.s(item.symbol))
    return group(tasks)()


@celery.task(bind=True, name="tasks.fetch_newsriver_update")
def newsriver_update(self):
    from app.finance_news.fetch import fetch_symbol
    has_more = True
    num_query = 0
    while has_more and num_query <= 15:
        has_more = fetch_symbol(publisher='seekingalpha.com', provider='newsriver')
    return True



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
