#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

from celery import group
from mongoengine import Q

from app.application import celery
# pylint: disable=invalid-name,unused-argument
from app.finance_news.models import FinanceNews, SyncStatus
from app.timeseries.fetch import fetch_daily_stock_data
from app.utils import chunks
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
def watson_analyze_webpage(self, username, password, url, html, content):
    from app.watson.analyze import analyze

    result = None
    try:
        print username
        result = analyze(username, password, url=url, html=html, content=content)
    except Exception as exc:
        logger.exception(exc)
        result = exc.message
    return result


@celery.task(bind=True, name="tasks.watson_analytics")
def watson_analytics(self):
    existing_urls = WatsonAnalytics.objects.distinct('url')
    credentials = []
    for i in xrange(1, 11):
        credentials.append((os.getenv('WATSON_USERNAME%s' % i), os.getenv('WATSON_PASSWORD%s' % i)))
    tasks = []
    query = Q(url__nin=existing_urls) & (Q(html__ne=None) | Q(content__ne=None))
    queryset = FinanceNews.objects(query).only('url', 'html', 'content').limit(
        30 * len(credentials))
    for idx, item in enumerate(queryset):
        username, password = credentials[idx % len(credentials)]
        if item.html or item.content:
            tasks.append(watson_analyze_webpage.s(username, password, item.url, item.html,
                                                  item.content))
    return group(tasks)()


@celery.task(bind=True, name='tasks.stock_daily_timeseries_data_fetch_symbol')
def stock_daily_timeseries_data_fetch_symbol(self, symbols):
    for symbol in symbols:
        status = SyncStatus.objects(symbol=symbol, provider='alphavantage').first()
        try:
            res = fetch_daily_stock_data(symbol, 'full')
        except Exception as e:
            print "error with symbol %s" % symbol
        status.has_more = False
        status.save()
    return True


@celery.task(bind=True, name="tasks.stock_daily_timeseries_data")
def stock_daily_timeseries_data(self):
    queryset = SyncStatus.objects(has_more=True, provider='alphavantage').distinct('symbol')
    tasks = []
    for symbols in list(chunks(queryset, 10)):
        if len(tasks) > 10:
            break
        tasks.append(stock_daily_timeseries_data_fetch_symbol.s(symbols))
    return group(tasks)()


@celery.task(bind=True, name="tasks.fetch_newsriver_update")
def fetch_newsriver_update(self):
    from app.finance_news.fetch import fetch_symbol
    has_more = True
    for i in xrange(0, 6):
        if not has_more:
            break
        num_query = 0
        while has_more and num_query <= 15:
            has_more = fetch_symbol(publisher='seekingalpha.com', provider='newsriver',
                                    token=os.getenv('NEWS_RIVER%s' % i))
    return True


@celery.task(bind=True, name="tasks.intrinio_company_news_fetch_symbol")
def intrinio_company_news_fetch_symbol(self, symbol, username, password):
    from app.finance_news.providers.intrinio_fetcher import IntrinioFetcher
    intrinio_fetcher = IntrinioFetcher(username=username, password=password)
    intrinio_fetcher.intrinio.client.cache_enabled = False
    intrinio_fetcher.fetch_company_news(symbol)
    return True


@celery.task(bind=True, name="tasks.intrinio_company_news")
def intrinio_company_news(self):
    queryset = SyncStatus.objects(
        has_more=True, provider='intrinio', publisher='company_news', symbol__ne=None).distinct(
        'symbol')
    tasks = []
    credentials = []
    for i in xrange(1, 3):
        credentials.append((os.getenv('INTRINIO_USERNAME%s' % i), os.getenv('INTRINIO_PASSWORD%s' %
                                                                           i)))
    for idx, symbol in enumerate(queryset):
        if len(tasks) > 10:
            break
        username, password = credentials[idx % len(credentials)]

        tasks.append(intrinio_company_news_fetch_symbol.s(symbol, username, password))
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
