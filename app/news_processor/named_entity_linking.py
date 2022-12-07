import requests
from flask import current_app
from mongoengine import NotUniqueError

from app.models.news_analytics import NewsAnalyticsProcessingState


def add_lemma_form_to_entity(spacy_json):
    ents, tokens = spacy_json["ents"], spacy_json["tokens"]
    for ent in ents:
        entity_tokens = [
            token
            for token in tokens
            if token["start"] >= ent["start"] and token["end"] <= ent["end"]
        ]
        ent["lemma"] = [item["lemma"] for item in entity_tokens]
        for token in entity_tokens:
            if token["pos"] == "VERB":
                ent["label"] = "ACTION"
                break
        offsets = []
        if ent["params"]["dbpedia_id"]:
            for token in tokens:
                if token["lemma"] in ent["lemma"]:
                    offsets.append(token["start"])
                    token["ent"] = ent["params"]["dbpedia_id"]
        ent["offsets"] = offsets
    return spacy_json


def _named_entity_linking(url):
    from app.models.news import News, NewsProcessingState
    from app.models.news_analytics import NewsAnalytics

    analytics = NewsAnalytics.objects(url=url).first()
    news = News.objects(url=url).first()
    nel_url = current_app.config["NEL_ENDPOINT"]

    try:
        text = news.snippet
        if news.title and text.find(news.title) == -1:
            text = f"{news.title}. {text}"
        resp = requests.post(url=nel_url, data={"input-text": text}).json()
        if not analytics:
            analytics = NewsAnalytics(url=url)
        if news.title:
            analytics.title = news.title
        else:
            analytics.title = text.split(". ")[0]
        analytics.publication_date = news.datetime
        analytics.source = news.source
        analytics.text = news.snippet
        analytics.version = int(resp.pop("version"))
        analytics.entity_html = resp.pop("html")
        analytics.spacy_json = add_lemma_form_to_entity(resp)
        analytics.processing_state = (
            NewsAnalyticsProcessingState.NAMED_ENTITY_LINKED.value
        )

        analytics.save()
        news.processing_state = NewsProcessingState.ANALYZED.value

    except NotUniqueError as exp:
        news.processing_state = NewsProcessingState.ANALYZED.value
    except ConnectionError as exp:
        print(exp)
    except Exception as exp:
        print(exp)
        current_app.logger.exception(exp, exc_info=True)
        news.processing_state = NewsProcessingState.ANALYZE_ERROR.value
    news.save()


def task_named_entity_linking(skip=0):
    """
    transform news into kg entities. results are stored in news_analytics
    :param skip:
    :return:
    """
    from mongoengine import Q

    from app.models.news import News, NewsProcessingState

    query = Q(processing_state=NewsProcessingState.CLEANED.value)
    item = News.objects(query).skip(skip).order_by("-datetime").first()
    while item:
        print(f"linking {item.url}")
        _named_entity_linking(item.url)
        item = News.objects(query).skip(skip).order_by("-datetime").first()
