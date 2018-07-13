import calendar
import json
import os
import time
import urllib
from datetime import datetime

import requests
from dateutil import parser
from pymongo import UpdateOne

from app.finance_news.models import Stock, SyncStatus
from app.utils import cache_api_response

PROVIDER = 'newsriver'


def init():
    symbols = Stock.objects.distinct('symbol')
    operations = []
    for symbol in symbols:
        for publisher in ['seekingalpha.com']:
            data = {
                'symbol': symbol,
                'publisher': publisher,
                'provider': PROVIDER,
                'backfill_start_date': datetime(2018, 1, 1),
                'backfill_end_date': datetime(2018, 7, 1)
            }
            operations.append(UpdateOne(
                {'symbol': symbol, 'publisher': publisher, 'provider': PROVIDER},
                {'$set': data},
                upsert=True))
    if operations:
        SyncStatus._get_collection().bulk_write(operations, ordered=False)



def query_news_update(publisher, date, token):
    """
    [
  {
    "id": "IFBnN_ai0fyjjXwF3lZ0zYi6niQj5YkXJjPlnk0LaEOVQ78TijG1t6gA0m_NxTmwwRVh5CFMjf9cIxHc9cvong",
    "publishDate": "2018-03-19T19:56:41",
    "discoverDate": "2018-03-19T21:39:00.820+0000",
    "title": "How Apple May Be Pulling Away From Android",
    "language": "en",
    "text": "Appl..."
    "structuredText": "<div>Apple...</div>",
    "url": "https://seekingalpha.com/article/4157621-apple-may-pulling-away-android",
    "elements": [
      {
        "type": "Image",
        "primary": true,
        "url": "https://static.seekingalpha.com/uploads/2018/3/18/7256021-1521420887159279.png",
        "width": null,
        "height": null,
        "title": null,
        "alternative": null
      }
    ],
    "website": {
      "name": "staticseekingalpha.a.ssl.fastly.net/",
      "hostName": "seekingalpha.com",
      "domainName": "seekingalpha.com",
      "iconURL": "https://staticseekingalpha2.a.ssl.fastly.net/assets/favicon-a2c6a902a7244e473d37b199d3051bcd31bce6384495593c944f72160559ceb9.svg",
      "countryName": "",
      "countryCode": "",
      "region": null
    },
    "metadata": {
      "finSentiment": {
        "type": "finSentiment",
        "sentiment": -0.02
      },
      "readTime": {
        "type": "readTime",
        "seconds": 546
      }
    },
    "highlight": " valuation. Background The thesis of this article is that <highlighted>AAPL</highlighted> may already be executing a plan that",
    "score": 16.876184
    }]
    :param keyword:
    :return:

    """
    query = "text: \"\" AND website.domainName: \"%s\" AND discoverDate:[%s TO *]" % (
            publisher, date.strftime('%Y-%m-%d'))
    params = {
        "query": query,
        "sortBy": "discoverDate",
        "sortOrder": "ASC",
        "limit": "100"
    }
    url = "https://api.newsriver.io/v2/search"
    url += "?query=" + urllib.urlencode(params)
    headers = {
        "Authorization": token}
    response = requests.get(url, headers=headers)
    results = []
    try:
        data = response.json()
        for item in data:
            date = item.get('publishDate', item['discoverDate'])
            timestamp = calendar.timegm(parser.parse(date).timetuple())
            result = {
                'url': item['url'],
                'content': item['text'],
                'html': item['structuredText'],
                'timestamp': int(timestamp),
                'title': item['title']
            }
            results.append(result)
    except Exception as e:
        print response.content
    return results
