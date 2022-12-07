import datetime
from urllib.parse import urlencode

import requests
from dateutil import parser
from flask import current_app

from app.models.news import News, NewsProcessingState
from app.news_importer import NewsImporterBase

# pylint: disable=line-too-long


class MediaStackImporter(NewsImporterBase):
    def __init__(self) -> None:
        super().__init__(source="aggregator")

    def fetch_documents(self):
        """
               {
        "pagination": {
          "limit": 100,
          "offset": 0,
          "count": 93,
          "total": 93
        },
        "data": [
          {
            "author": null,
            "title": "One Texas deputy killed and two others wounded in shooting, Houston police say",
            "description": "A constable\u0027s deputy was killed and two others were wounded when they were shot from behind outside a bar in Houston, Texas, early Saturday, authorities said.",
            "url": "http:\\/\\/rss.cnn.com\\/~r\\/rss\\/cnn_latest\\/~3\\/VZfPei3TADo\\/index.html",
            "source": "CNN",
            "image": "https:\\/\\/cdn.cnn.com\\/cnnnext\\/dam\\/assets\\/150325082132-social-gfx-breaking-news-super-169.jpg",
            "category": "general",
            "language": "en",
            "country": "us",
            "published_at": "2021-10-16T10:50:11+00:00"
          }]
          }
                :param keyword:
                :return:

        """
        existing_urls = News.objects(source=self.source).distinct("url")

        date = datetime.datetime.utcnow() - datetime.timedelta(days=1)
        params = {
            "languages": "en",
            "sources": "bbc,cnn,nyt,ft,reuters,bloomberg",
            "date": date.strftime("%Y-%m-%d"),
            "limit": 100,
            "sort": "published_desc",
            "offset": 0,
            "access_key": current_app.config["MEDIA_STACK"],
        }
        url = "http://api.mediastack.com/v1/news"
        url += "?" + urlencode(params)
        response = requests.get(url)
        results = []
        try:
            data = response.json()

            for item in data["data"]:
                if not item["description"]:
                    continue
                cleaned_url = item["url"].split("?")[0]
                if item["url"] in existing_urls or cleaned_url in existing_urls:
                    continue
                date = parser.parse(item.get("published_at"))
                result = {
                    "url": cleaned_url,
                    "content": item["description"],
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
        news = News.objects(url=url, source=self.source).first()
        if not news:
            return

        title = news["title"]
        content = news["content"]

        tokens = title.split(" ", 1)
        if len(tokens) > 1:
            title = " ".join([tokens[0], tokens[1].lower()])

        snippet = title
        if snippet[-1] != ".":
            snippet += ". "
        else:
            snippet += " "

        if snippet.lower().find(content.lower()) == -1:
            snippet += content

        news.snippet = snippet
        news.save()
