from app.admin.base import AuthModelView
from app.admin.manual_cron import ManualCronView
from app.finance_news.admin import FinanceNewsView
from app.finance_news.models import FinanceNews
from app.watson.admin import WatsonAnalyticsView
from app.watson.models import WatsonAnalytics, Category, Entity, Concept, Keyword, Author


def add_admin_views(admin):
    #admin.add_view(FinanceNewsView(FinanceNews))

    admin.add_view(WatsonAnalyticsView(WatsonAnalytics))
    for model in [Category, Entity, Author, Concept]:
        admin.add_view(AuthModelView(model))

   # admin.add_view(ManualCronView(name='Cron'))

