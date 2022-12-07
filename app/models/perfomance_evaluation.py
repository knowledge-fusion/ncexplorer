from mongoengine import (
    CASCADE,
    BooleanField,
    DictField,
    FloatField,
    IntField,
    ListField,
    ReferenceField,
    StringField,
)

from app.common.mongoengine_base import BaseDocument

# pylint: disable=line-too-long
from app.models.document_pattern import DocumentPattern
from app.models.news_analytics import NewsAnalytics


class PerformanceEvaluation(BaseDocument):
    news_analytics = ReferenceField(
        NewsAnalytics, required=True, reverse_delete_rule=CASCADE, unique=True
    )
    source = StringField()
    tokenize_time = FloatField()
    nel_time = FloatField()
    category_expansion = FloatField()
    entity_relevance_calculation = FloatField()
    abstraction_relevance_calculation = FloatField()
    vector_calculation = FloatField()
    connectivity_score_sampling = FloatField()
    connectivity_score_no_sampling = FloatField()
    connectivity_score_execution_time = FloatField()


class QueryPerformanceEvaluation(BaseDocument):
    name = StringField(required=True, unique=True)
    lucene_processing_time = FloatField()
    bert_processing_time = FloatField()
    newslink_processing_time = FloatField()
    newslink_bert_processing_time = FloatField()
    dora_processing_time = FloatField()
    lucene_retrieval_time = FloatField()
    bert_retrieval_time = FloatField()
    newslink_retrieval_time = FloatField()
    newslink_bert_retrieval_time = FloatField()
    ncexplorer_retrieval_time = FloatField()
    domain = StringField(choices=["business", "politics"])
    extra_data = DictField()

    def __unicode__(self):
        return self.name


class SubdomainRecommendationEvaluation(BaseDocument):
    name = StringField(required=True, unique=True)
    top_coverage_subdomain = StringField()
    top_coverage_document_count = IntField()
    top_coverage_specificity_subdomain = StringField()
    top_coverage_specificity_document_count = IntField()
    # top_coverage_diversity_subdomain = StringField()
    top_coverage_specificity_diversity_subdomain = StringField()
    top_coverage_specificity_diversity_document_count = IntField()
    top_coverage_specificity_diversity_distinct_entity_count = IntField()
    diversity_score = FloatField()
    all_subdomain_records = ListField(DictField())
    distinct_top_subdomains = IntField()

    selected_for_survey = BooleanField()

    def __unicode__(self):
        return self.name

    def subdomain_documents(self, subdomain, entities=None):
        from app.models.document_entity_category import DocumentEntityCategory

        print(f"{subdomain}-{entities}")
        item = [
            item
            for item in self.all_subdomain_records
            if subdomain == item["abstraction"]
        ]
        document_htmls = []
        related_entities = set()
        if item:
            record = item[0]
            document_entity_category = DocumentEntityCategory.objects(
                news_analytics__in=record["documents"]
            )
            if entities:
                document_entity_category = document_entity_category.filter(
                    entity__in=entities
                )

            for document in record["documents"]:
                entity_abstraction_map = dict()
                for entity_category in document_entity_category.filter(
                    category__in=[record["abstraction"]] + self.name.split(","),
                    news_analytics=document,
                ):
                    entity_abstraction_map[
                        entity_category.entity
                    ] = entity_category.category.split(":")[-1].replace("_", " ")
                    if entity_category.category == subdomain:
                        related_entities.add(entity_category.entity)
                html = entity_category.news_analytics.render_spacy_entity_html(
                    entity_abstraction_map=entity_abstraction_map, add_explaination=True
                )
                document_htmls.append(html)
        return document_htmls, list(related_entities)

    def extra_view(self):
        res = ""
        from app.models.document_pattern import DocumentPattern

        document_pattern = DocumentPattern.objects(name=self.name).first()
        documents = document_pattern.documents

        from app.models.document_entity_category import DocumentEntityCategory

        document_entity_category = DocumentEntityCategory.objects(
            news_analytics__in=documents
        )

        for subdomain in [
            self.top_coverage_subdomain,
            self.top_coverage_specificity_subdomain,
            self.top_coverage_specificity_diversity_subdomain,
        ]:

            record = [
                item
                for item in self.all_subdomain_records
                if subdomain == item["abstraction"]
            ][0]

            res += f"<br><br><b>{record['abstraction']}</b> count: {len(record['documents'])}, coverage: {record['coverage']}, specificity: {record['specificity']},"
            res += f"diversity {record['diversity']}, total {round(record['coverage_specificity_diversity'], 2)}<br/>"
            res += f"{', '.join(list(set(record['entities'])))}<br><br>"

            res += "<ul>"

            documents_html, related_entities = self.subdomain_documents(
                subdomain=subdomain
            )
            for idx, document_html in enumerate(documents_html):
                res += f"<li>{idx + 1}. {document_html}"
                res += "</li>"
                if idx > 10:
                    break
            res += "</ul>"

        return res


class ContextRelevanceScoreEvaluation(BaseDocument):
    news_analytics = ReferenceField(
        NewsAnalytics, required=True, reverse_delete_rule=CASCADE
    )
    version = IntField()
    source = StringField()
    entity = StringField()
    category = StringField(unique_with="news_analytics")
    concept_entities = ListField(StringField())
    context_entities = ListField(StringField())
    pair_count = IntField()

    incorrect_entity = StringField()
    incorrect_category = StringField()

    correct_connectivity_scores = DictField()
    incorrect_connectivity_scores = DictField()

    correct_connectivity_scores_v2 = DictField()
    incorrect_connectivity_scores_v2 = DictField()

    correct_connectivity_score = FloatField()
    incorrect_connectivity_score = FloatField()

    connectivity_scores_with_sampling = ListField(FloatField())
    connectivity_scores_no_sampling = ListField(FloatField())
    sampling_execution_time = FloatField()
    no_sampling_execution_time = FloatField()
    connectivity_score_no_sampling = FloatField()

    targeted_sampling_estimates = DictField()
    targeted_sampling_time = FloatField()
    targeted_sampling_errors = ListField(FloatField())

    sampling_no_reachability_index_estimates = DictField()
    sampling_no_reachability_index_errors = ListField(FloatField())

    random_sampling_estimates = DictField()
    random_sampling_time = FloatField()
    random_sampling_errors = ListField(FloatField())

    def __unicode__(self):
        return f"{self.category} {self.context_entities}"


class ContextRelevanceScoreEvaluationReachabilityIndex(BaseDocument):
    evaluation = ReferenceField(
        ContextRelevanceScoreEvaluation,
        required=True,
        reverse_delete_rule=CASCADE,
        unique=True,
    )
    reachable_graph = DictField()
    reachable_graph_time = FloatField()


class PathCountSamplingEvaluation(BaseDocument):
    concept_entity = StringField(required=True)
    instance_entity = StringField(required=True, unique_with="concept_entity")
    path_length = IntField(required=True)
    reachable_graph_probabilities = ListField(FloatField())
    ground_truth_paths_count = IntField()
    ground_truth_paths = ListField(ListField(StringField()))
    sample_count = IntField(default=0)
    running_errors = ListField(FloatField())
    estimation_mean = FloatField()
    delta = FloatField()  # 95%
    standard_error_of_mean = FloatField()
    error_from_ground_truth = FloatField()
    skip = BooleanField()
    brute_force_computation_time = IntField()
    brute_force_computation_time2 = FloatField()

    @classmethod
    def get_filter(cls, record):
        flt = {
            "concept_entity": record.pop("concept_entity"),
            "instance_entity": record.pop("instance_entity"),
        }

        return flt

    def __unicode__(self):
        return f"from {self.concept_entity} to {self.instance_entity}: {self.ground_truth_paths_count}"


class SubdomainRecommendationSurveyResult(BaseDocument):
    evaluation_session = StringField(unique=True)
    ip_address = StringField()
    answers = DictField()
