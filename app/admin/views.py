from app.admin.base import AuthModelView
from app.finance_news.admin import FinanceNewsView
from app.finance_news.models import FinanceNews, Stock, SyncStatus
from app.timeseries.models import StockDailyTimeSeries, EconomicIndex
from app.watson.admin import WatsonAnalyticsView
from app.watson.models import WatsonAnalytics, Category, Entity, Concept, Author


def add_admin_views(admin):
    admin.add_view(FinanceNewsView(FinanceNews))
    admin.add_view(AuthModelView(Stock))
    admin.add_view(AuthModelView(SyncStatus))

    admin.add_view(WatsonAnalyticsView(WatsonAnalytics))
    for model in [Category, Entity, Author, Concept]:
        admin.add_view(AuthModelView(model))

    admin.add_view(AuthModelView(StockDailyTimeSeries))
    admin.add_view(AuthModelView(EconomicIndex))
