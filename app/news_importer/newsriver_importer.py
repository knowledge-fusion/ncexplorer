from urllib.parse import urlencode

import requests
from dateutil import parser
from flask import current_app

from app.models.news import News, NewsProcessingState
from app.news_importer import NewsImporterBase

# pylint: disable=line-too-long


class NewsRiverImporter(NewsImporterBase):
    def __init__(self, token) -> None:
        self.token = token
        super().__init__(source="newsriver")

    def fetch_documents(self):
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
        query = "language:EN"
        params = {
            "query": query,
            "sortBy": "_score",
            "sortOrder": "DESC",
            "limit": "100",
        }
        url = "https://api.newsriver.io/v2/search"
        url += "?" + urlencode(params)
        headers = {"Authorization": self.token}
        response = requests.get(url, headers=headers)
        results = []
        try:
            data = response.json()

            for item in data:
                date = parser.parse(item.get("publishDate", item["discoverDate"]))
                result = {
                    "url": item["url"],
                    "content": item["text"],
                    "html": item["structuredText"],
                    "title": item["title"],
                    "datetime": date,
                    "source": self.source,
                    "processing_state": NewsProcessingState.CLEANED.value,
                }
                results.append(result)
            if results:
                News.upsert_many(results)
        except Exception as e:
            current_app.logger.error(e, extra={"content": response.content})
        print(f"fetch {len(results)} news_importer")
        return results

    def clean_document(self, url):
        pass
