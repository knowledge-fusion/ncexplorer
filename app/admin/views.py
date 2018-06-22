from flask_admin.contrib.mongoengine import ModelView

from app.finance_news.admin import FinanceNewsView
from app.finance_news.models import FinanceNews
from app.watson.models import WatsonAnalytics, Category, Entity, Concept


def add_admin_views(admin):
    admin.add_view(FinanceNewsView(FinanceNews))

    admin.add_view(ModelView(Category))
    admin.add_view(ModelView(Entity))
    admin.add_view(ModelView(
        Concept
    ))

    admin.add_view(ModelView(WatsonAnalytics))