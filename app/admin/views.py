from app.admin.base import AuthModelView
from app.common.models import SystemConfig
from app.models.admin import (
    DBPediaEntityAliasView,
    DocumentEntityCategoryView,
    DocumentPatternView,
    NewsAnalyticsView,
    NewsView,
    PathCountSamplingEvaluationView,
    SubdomainRecommendationEvaluationView,
)
from app.models.dbpedia_category import DBPediaCategory, DBPediaCategoryHierarchy
from app.models.dbpedia_entity_alias import DBPediaEntityAlias
from app.models.dbpedia_entity_category import DBPediaEntityCategory
from app.models.dbpedia_entity_linked_attribute import DBPediaEntityLinkedAttribute
from app.models.dbpedia_entity_tag import DBPediaEntityTag
from app.models.dbpedia_entity_wikilink import DBPediaEntityWikilink
from app.models.document_entity import DocumentEntity
from app.models.document_entity_category import DocumentEntityCategory
from app.models.document_pattern import DocumentPattern
from app.models.document_pattern_evaluation import (
    DocumentPatternEvaluation,
    DocumentPatternEvaluationQuestion,
)
from app.models.news import News
from app.models.news_analytics import NewsAnalytics
from app.models.outstanding_fact import OutstandingFact
from app.models.perfomance_evaluation import (
    ContextRelevanceScoreEvaluation,
    PathCountSamplingEvaluation,
    PerformanceEvaluation,
    QueryPerformanceEvaluation,
    SubdomainRecommendationEvaluation,
    SubdomainRecommendationSurveyResult,
)
from app.models.stock_data_models import EconomicIndex, Stock, StockDailyTimeSeries
from app.models.utility_models import SyncStatus


def add_admin_views(admin):
    utils = "Utils"
    stock = "Stock"
    evaluation = "Evaluation"

    admin.add_view(NewsAnalyticsView(NewsAnalytics))
    admin.add_view(NewsView(News))
    admin.add_view(AuthModelView(DocumentEntity))
    admin.add_view(DocumentEntityCategoryView(DocumentEntityCategory))
    admin.add_view(DocumentPatternView(DocumentPattern))
    admin.add_view(AuthModelView(DBPediaCategoryHierarchy))
    admin.add_view(AuthModelView(DBPediaEntityCategory))
    admin.add_view(AuthModelView(DBPediaEntityLinkedAttribute))
    admin.add_view(AuthModelView(DBPediaEntityWikilink))
    admin.add_view(AuthModelView(DBPediaCategory))
    admin.add_view(DBPediaEntityAliasView(DBPediaEntityAlias))

    admin.add_view(
        DocumentPatternView(DocumentPatternEvaluationQuestion, category=evaluation)
    )
    admin.add_view(AuthModelView(DocumentPatternEvaluation, category=evaluation))
    admin.add_view(AuthModelView(OutstandingFact, category=evaluation))
    admin.add_view(AuthModelView(PerformanceEvaluation, category=evaluation))
    admin.add_view(AuthModelView(QueryPerformanceEvaluation, category=evaluation))
    admin.add_view(AuthModelView(ContextRelevanceScoreEvaluation, category=evaluation))
    admin.add_view(
        SubdomainRecommendationEvaluationView(
            SubdomainRecommendationEvaluation, category=evaluation
        )
    )

    admin.add_view(
        PathCountSamplingEvaluationView(
            PathCountSamplingEvaluation, category=evaluation
        )
    )
    admin.add_view(
        AuthModelView(SubdomainRecommendationSurveyResult, category=evaluation)
    )
    admin.add_view(AuthModelView(Stock, category=stock))
    admin.add_view(AuthModelView(StockDailyTimeSeries, category=stock))
    admin.add_view(AuthModelView(EconomicIndex, category=stock))

    admin.add_view(AuthModelView(SystemConfig, category=utils))
    admin.add_view(AuthModelView(SyncStatus, category=utils))
    admin.add_view(AuthModelView(DBPediaEntityTag, category=utils))
