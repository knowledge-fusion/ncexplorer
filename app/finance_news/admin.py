from gettext import gettext

from flask_admin.contrib.mongoengine.filters import BaseMongoEngineFilter
from flask_admin.contrib.mongoengine.tools import parse_like_term

from app.admin.base import AuthModelView
from app.finance_news.models import FinanceNews, Stock


class FinanceSymbolFilter(BaseMongoEngineFilter):

    def apply(self, query, value):
        term, data = parse_like_term(value)

        flt = {'%s__%s' % (FinanceNews.symbol.name, term): data}

        res = FinanceNews.objects.filter(**flt).only('id')
        ids = [str(item.id) for item in res]
        flt2 = {'%s__in' % (self.column.name): ids}
        return query.filter(**flt2)

    def operation(self):
        return gettext('like')

    # You can validate values. If value is not valid,
    # return `False`, so filter will be ignored.
    def validate(self, value):
        return True

    # You can "clean" values before they will be
    # passed to the your data access layer
    def clean(self, value):
        return value


def symbol_filter(filter_column):
    results = Stock.objects.distinct("symbol")
    options = [(item, item) for item in results]
    return FinanceSymbolFilter(filter_column, 'Symbol', options=options)


class FinanceNewsView(AuthModelView):
    column_display_pk = False
    column_list = ('symbol', 'title', 'timestamp', 'source')

    column_searchable_list = ['symbol', 'title']
    column_filters = (
        symbol_filter(FinanceNews.id),
    )
