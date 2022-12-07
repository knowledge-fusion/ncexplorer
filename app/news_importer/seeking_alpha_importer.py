import os

from bs4 import BeautifulSoup
from flask import current_app

from app.models.news import News, NewsProcessingState
from app.news_importer import NewsImporterBase


class SeekingAlphaImporter(NewsImporterBase):
    def __init__(self) -> None:
        super().__init__(source="seekingalpha")

    def clean_document(self, url):
        news = News.objects(url=url).first()

        if "filing" in url:
            news.processing_state = NewsProcessingState.SKIPPED.value
            news.save()
            return

        html_doc = news.html
        soup = BeautifulSoup(html_doc, "html.parser")
        html = soup.find(id="bullets_ul")
        if not html:
            html = soup.find(id="main_content")
        if not html:
            # current_app.logger.error("cannot parse url %s" % url)
            news.processing_state = NewsProcessingState.SKIPPED.value
            news.save()
            return
        stop_words = ["Click to subscribe", "Previously:", "See all stocks on the move"]
        text = os.linesep.join([s.strip() for s in html.get_text().splitlines() if s])
        if text:
            for stop_word in stop_words:
                idx = text.lower().find(stop_word.lower())
                while idx > 0:
                    text = text[0:idx]
                    idx = text.lower().find(stop_word.lower())
            if text.find("SA News Editor") > -1:
                text = text.split("SA News Editor")[-1]
            news.content = text.strip()
            news.processing_state = NewsProcessingState.CLEANED.value
            self.extract_snippet(news)
            news.save()
        else:
            news.processing_state = NewsProcessingState.SKIPPED.value
            news.save()
            print(f"cannot extract content {url}")

    def fetch_documents(self):
        query = News.objects(
            url__startswith="https://seekingalpha.com", html__ne=None, content=""
        ).only("url")
        # TODO craw the news page
        for news in query:
            url = news.url
            self.clean_document(url)
            print(f"done {url}")

    def extract_snippet(self, news_or_url):
        # "UPDATE 1-TransCanada temporarily cuts tariffs on Cushing-Texas pipeline - FERC"

        news = news_or_url
        if not hasattr(news_or_url, "id"):
            news = News.objects(url=news_or_url).first()
        id = news.id
        title = news.title.strip()
        if title.find("-"):
            # filter caps e.g.
            token = title.split("-")[0]
            if token == token.upper():
                title = title[title.find("-") + 1 :]

        if title[-1] != ".":
            title = f"{title}. "

        text = news.content.strip()
        if text.find(". ") == -1:
            text = text.replace("\n", ". ")
        else:
            text = text.replace("\n", " ")
        text = text.replace("**", ". ")
        text = text.replace("* ", ". ")
        if not text:
            from app.models.news_analytics import NewsAnalytics

            item = NewsAnalytics.objects(url=news.url).first()
            if item:
                item.delete()
            news.delete()
            return
        if ". " in text:
            sentences = text.split(". ")
        else:
            current_app.logger.error(f"cannot find delimiter for url {news.id}")
            sentences = text.split(".")

        snippet = title
        idx = 0
        if sentences and sentences[idx].find(title.strip()) > -1:
            idx += 1

        while len(snippet) < 100 and len(sentences) - 1 > idx:
            sentence = sentences[idx].strip()
            if not sentence:
                idx += 1
                continue
            if sentence[-1] == ".":
                snippet += f"{sentence}"
            else:
                snippet += f"{sentence}."
            idx += 1
        news.processing_state = NewsProcessingState.CLEANED.value
        news.snippet = snippet
        news.save()
