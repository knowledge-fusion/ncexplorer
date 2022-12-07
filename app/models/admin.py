from gettext import gettext

from flask_admin.contrib.mongoengine import filters
from flask_admin.contrib.mongoengine.filters import BaseMongoEngineFilter
from flask_admin.contrib.mongoengine.tools import parse_like_term

from app.admin.base import AuthModelView
from app.models.abstraction_cooccurence_count import AbstractionCooccurrenceCount
from app.models.news import News
from app.models.stock_data_models import Stock
from app.utils import flask_admin_select_filter


class NewsAnalyticsView(AuthModelView):
    column_searchable_list = ["url", "title"]
    details_template = "admin/news_analytics_detail_view.html"
    column_exclude_list = ["extra_data"]
    column_editable_list = ["title"]
    column_details_exclude_list = [
        "spacy_doc",
        "spacy_json",
        "hash_digest",
        "authors",
        "sadness",
        "joy",
        "fear",
        "disgust",
        "anger",
        "entity_abstractions",
        "_abstraction_graph",
        "connect_component_analyzed",
        "vector",
    ]
    column_list = [
        "url",
        "title",
        "publication_date",
        "recognized_entities",
        "sentiment_score",
        "processing_state",
        "source",
        "version",
        "updated_at",
    ]


class SymbolFilter(BaseMongoEngineFilter):
    def apply(self, query, value):
        term, data = parse_like_term(value)

        flt = {f"{News.symbol.name}__{term}": data}

        res = News.objects.filter(**flt).only("id")
        ids = [str(item.id) for item in res]
        flt2 = {"%s__in" % (self.column.name): ids}
        return query.filter(**flt2)

    def operation(self):
        return gettext("like")

    # You can validate values. If value is not valid,
    # return `False`, so filter will be ignored.
    def validate(self, value):
        return True

    # You can "clean" values before they will be
    # passed to the your data access layer
    def clean(self, value):
        return value


def symbol_filter(filter_column):
    results = []
    try:
        results = Stock.objects.distinct("symbol")
    except Exception:
        pass
    options = [(item, item) for item in results]
    return SymbolFilter(filter_column, "Symbol", options=options)


class DocumentEntityCategoryView(AuthModelView):
    column_exclude_list = ["kg_paths"]


class SubdomainRecommendationEvaluationView(AuthModelView):
    column_exclude_list = ["all_subdomain_records"]


class DocumentPatternView(AuthModelView):
    column_searchable_list = ["name"]
    column_exclude_list = [
        "documents",
        "document_bert_score",
        "created_at",
        "version",
        "bm25_cosine_similarity_result",
        "bert_cosine_similarity_result",
        "abstract_search_result",
        "news_link_entities",
        "news_link_result",
        "newslink_bert_cosine_similarity_result",
        "kg_entities",
    ]

    column_details_exclude_list = [
        "news_link_entities",
        "news_link_result",
        "document_bert_score",
        "kg_entities",
    ]


class NewsView(AuthModelView):
    details_template = "admin/safe_detail_view.html"
    column_display_pk = False
    column_list = (
        "title",
        "source",
        "datetime",
        "processing_state",
        "updated_at",
        "url",
    )

    column_searchable_list = ["url", "title"]
    column_filters = (
        symbol_filter(News.id),
        flask_admin_select_filter(News.source),
        flask_admin_select_filter(News.processing_state),
    )


class AbstractionCooccurrenceCountView(AuthModelView):
    column_exclude_list = ["documents", "simple_paths"]

    column_filters = (
        filters.FilterEmpty(
            AbstractionCooccurrenceCount.documents,
            AbstractionCooccurrenceCount.documents.name,
        ),
        filters.FilterEmpty(
            AbstractionCooccurrenceCount.simple_paths,
            AbstractionCooccurrenceCount.simple_paths.name,
        ),
    )
    column_searchable_list = ["abstraction_pair"]


class DBPediaEntityAliasView(AuthModelView):
    column_list = (
        "updated_at",
        "subject",
        "derived_type",
        "type",
        "hypernym",
        "infobox_template",
        "dbpedia_hypernyms",
        "wikidata_id",
        "entity_type",
        "hypernyms",
        "processing_state",
        "kg_node_degree",
        "version",
        "link",
    )


class PathCountSamplingEvaluationView(AuthModelView):
    column_exclude_list = [
        "ground_truth_paths",
        "reachable_graph_probabilities",
        "running_errors",
    ]
