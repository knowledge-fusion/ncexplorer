import requests
from dateutil import parser
from flask import current_app

from app.models.news import News, NewsProcessingState
from app.news_importer import NewsImporterBase

# pylint: disable=line-too-long


class NewYorkTimesImporter(NewsImporterBase):
    def __init__(self, key) -> None:
        self.key = key
        super().__init__(source="nyt")

    def fetch_documents(self):
        """

        :param
        :return:

        """
        from datetime import datetime

        from app.common.models import SystemConfig

        key = "nyt_fetched_archives"
        config = SystemConfig.objects(key=key).first()
        fetched = set()

        if config:
            fetched = set(config.value.split(","))
        else:
            config = SystemConfig(key=key)
        now = datetime.utcnow()
        idx = 0

        self.fetch_archive(year=now.year, month=now.month)
        config.value = ",".join(fetched)
        config.save()
        return True

    def fetch_archive(self, year, month):
        existing_urls = News.objects(source=self.source).distinct("url")
        print(f"fetch nyt archive for year {year} month {month}")
        url = f"https://api.nytimes.com/svc/archive/v1/{year}/{month}.json?api-key={self.key}"
        response = requests.get(url)
        results = []
        try:
            data = response.json()
            docs = data["response"]["docs"]
            for item in docs:
                if not item.get("type_of_material") in ["News"]:
                    continue
                if item.get("web_url") in existing_urls:
                    continue
                if item["section"] in ["Corrections"]:
                    continue
                date = parser.parse(item.pop("pub_date"))
                result = {
                    "url": item.pop("web_url"),
                    "content": item.pop("abstract") + " " + item.pop("lead_paragraph"),
                    "title": item["headline"]["main"],
                    "datetime": date,
                    "source": self.source,
                    "processing_state": NewsProcessingState.CLEANED.value,
                    "extra_data": item,
                }
                results.append(result)
            if results:
                News.upsert_many(results)
        except Exception as e:
            current_app.logger.error(e, extra={"content": response.content})
        print(f"fetch {len(results)} news_importer")
        return results

    def fetch_latest(self):
        existing_urls = News.objects(source=self.source).distinct("url")

        url = f"https://api.nytimes.com/svc/news/v3/content/all/all.json?api-key={self.key}"
        response = requests.get(url)
        results = []
        try:
            data = response.json()
            docs = data["results"]
            for item in docs:
                if not item["material_type_facet"] in ["News"]:
                    continue
                if item["section"] in ["Corrections"]:
                    continue
                if item["url"] in existing_urls:
                    continue
                date = parser.parse(item.pop("published_date"))
                result = {
                    "url": item.pop("url"),
                    "content": item.pop("abstract"),
                    "title": item.pop("title"),
                    "datetime": date,
                    "source": self.source,
                    "processing_state": NewsProcessingState.CLEANED.value,
                    "extra_data": item,
                }
                results.append(result)
            if results:
                res = News.upsert_many(results)
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

        if snippet.find(content) == -1:
            snippet += content

        news.snippet = snippet
        news.save()
