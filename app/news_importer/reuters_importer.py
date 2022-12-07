from flask import current_app

from app.models.news import News, NewsProcessingState
from app.news_importer import NewsImporterBase


class ReutersImporter(NewsImporterBase):
    def __init__(self) -> None:
        super().__init__(source="reuters")

    def fetch_documents(self):
        import rarfile
        import xmltodict
        from dateutil import parser

        filenames = [
            "newsarchive/RTRS-201405.xml",
            "newsarchive/RTRS-201406.xml",
            "newsarchive/RTRS-201407.xml",
            "newsarchive/RTRS-201408.xml",
            "newsarchive/RTRS-201409.xml",
            "newsarchive/RTRS-201410.xml",
            "newsarchive/RTRS-201411.xml",
        ]
        count = 0
        with rarfile.RarFile("/home/wangsha/data/news-archieve/news-archive.rar") as rf:
            for filename in filenames:
                with rf.open(filename, "r") as f:
                    xmlString = ""
                    for line in f:
                        if not isinstance(line, str):
                            line = line.decode()
                        line = line.strip()
                        xmlString += line
                        if xmlString.endswith("</ContentEnvelope>"):
                            try:
                                object = xmltodict.parse(xmlString)["ContentEnvelope"]
                                count += 1
                                timestr = object["Header"]["Info"]["TimeStamp"]
                                time = parser.parse(timestr)
                                customId = object["Header"]["Info"]["Id"]
                                title = object["Body"]["ContentItem"]["Data"][
                                    "newsItem"
                                ]["contentMeta"]["headline"]
                                body = object["Body"]["ContentItem"]["Data"][
                                    "newsItem"
                                ]["contentSet"]["inlineXML"]["xhtml"].get("body", "")
                                lang = object["Body"]["ContentItem"]["Data"][
                                    "newsItem"
                                ]["contentMeta"]["language"]["@tag"]
                                xmlString = ""
                                skip = False
                                for skipped_title in [
                                    "standings",
                                    "  results",
                                    "BUZZ-",
                                    "TECHNICALS-",
                                    "SNAPSHOT-",
                                    "UPDATE ",
                                    "CORRECTED",
                                    "REFILE-",
                                    "*TOP NEWS*",
                                    "DIARY-",
                                    "PRESS DIGEST-",
                                    "SHH Margin Trading",
                                    "TABLE",
                                    "new issue index",
                                ]:
                                    if title.find(skipped_title) > -1:
                                        skip = True
                                        break

                                if skip:
                                    continue

                                if not body:
                                    continue
                                stop_words = [
                                    "(To read more",
                                    "For more details, click",
                                    "(Editing by",
                                    "You can also read",
                                    "Detailed PMI data",
                                    "To subscribe to the full data",
                                    "For further information",
                                    "FEATURES/INSIGHT",
                                    "Spot Rate",
                                    "Source text for",
                                    "(Additional reporting by",
                                    "Source text:",
                                    "(Reporting by",
                                ]
                                for stop_word in stop_words:
                                    body = body.split(stop_word)[0]
                                if body and len(body) > 500 and lang == "en":
                                    data = {
                                        "url": customId,
                                        "datetime": time,
                                        "title": title,
                                        "html": body,
                                        "source": self.source,
                                        "extra_data": object,
                                        "processing_state": NewsProcessingState.IMPORTED.value,
                                    }
                                    News.upsert(data)
                                    print(title)
                            except Exception as exp:
                                current_app.logger.error(exp, exc_info=True)
                                xmlString = ""

    def clean_document(self, url):
        news = News.objects(url=url).first()
        news.html = news.content
        try:
            raw = news.content.split("\n")[1:-7]
            raw[0] = " ".join(raw[0].split(" - ")[1:])
            content = "\n".join(raw)
            news.content = content
            news.processing_state = NewsProcessingState.CLEANED.value
        except Exception as exp:
            current_app.logger.exception(exp)
            news.processing_state = NewsProcessingState.SKIPPED.value
        news.save()
        self.extract_snippet(news)

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

        if title.find(" - ") > -1:
            # remove source
            title = title.split(" - ")[0]
        if title.find("UPDATE") > -1:
            tokens = title.split("UPDATE")
            title = [token for token in tokens if token][0]
            idx = title.find("-")
            if idx > -1:
                title = title[idx + 1 :]
        if not title:
            news.processing_state = NewsProcessingState.SKIPPED.value
            news.save()
            return
        if title[-1] != ".":
            title = f"{title}. "

        text = news.content.strip() if news.content else news.html.strip()
        if text.find("(Reuters") > -1:
            if text.find(" - ") > -1:
                text = text.split(" - ")[1]
            else:
                text = text.split(")")[1]
        if text.find("(Fitch)") > -1:
            text = text.split("(Fitch)")[-1]
        if text.find(".") == -1:
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
            sentences = text.split(".")

        snippet = title
        idx = 0

        while len(snippet) < 100 and len(sentences) - 1 > idx:
            sentence = sentences[idx].strip()
            if not sentence:
                idx += 1
                continue
            if snippet.find(sentence) > -1:
                idx += 1
                continue

            if sentence[-1] == ".":
                snippet += f"{sentence} "
            else:
                snippet += f"{sentence}. "
            idx += 1
        if len(snippet) <= 500:
            news.processing_state = NewsProcessingState.CLEANED.value
            news.snippet = snippet
        else:
            news.processing_state = NewsProcessingState.SKIPPED.value

        news.save()
