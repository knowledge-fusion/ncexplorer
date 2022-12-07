import requests
from flask import current_app


def task_batch_calculate_document_sentiment_score():
    from app.models.news_analytics import NewsAnalytics

    queryset = NewsAnalytics.objects(sentiment_score=None).limit(100)
    url = current_app.config["SENTIMENT_ANALYSIS_SERVICE"]
    while queryset:
        data = [item.text for item in queryset]
        urls = [item.url for item in queryset]
        from app.models.news_analytics import NewsAnalytics

        res = requests.post(url=url, json=data, timeout=150)
        updates = []
        for idx, sentiment in enumerate(res.json()):
            score = sentiment["score"]
            if sentiment["label"] == "NEG":
                score = -score
            if sentiment["label"] == "NEU":
                score = 0
            updates.append({"url": urls[idx], "sentiment_score": score})
        res = NewsAnalytics.upsert_many(updates)
        print(f"sentiment_score {updates[0]} {res=}")
        queryset = NewsAnalytics.objects(sentiment_score=None).limit(100)
