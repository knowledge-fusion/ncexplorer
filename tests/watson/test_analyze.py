import os

from app.finance_news.models import FinanceNews
from app.tasks import watson_analytics
from app.watson.analyze import analyze
from app.watson.models import WatsonAnalytics


def test_watson_analytics(app):
    watson_analytics()


def test_natual_language_understanding(app):
    existing_urls = WatsonAnalytics.objects.distinct('url')
    item = FinanceNews.objects(url__nin=existing_urls, html__ne=None).only('url', 'html').first()
    i = 3
    res = analyze(
        username=os.getenv('WATSON_USERNAME%s' % i),
        password=os.getenv('WATSON_PASSWORD%s' % i),
        url=item.url,
        html=item.html
    )
