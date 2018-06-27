from app.finance_news.models import FinanceNews
from app.watson.analyze import analyze
from app.watson.models import WatsonAnalytics


def test_natual_language_understanding(app):
    existing_urls = WatsonAnalytics.objects.distinct('url')
    item = FinanceNews.objects(url__nin=existing_urls).only('url', 'html').first()
    res = analyze(url=item.url, html=item.html)