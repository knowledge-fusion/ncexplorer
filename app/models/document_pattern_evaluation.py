from mongoengine import BooleanField, DictField, ListField, ReferenceField, StringField

from app.common.mongoengine_base import BaseDocument
from app.models.news_analytics import NewsAnalytics


class DocumentPatternEvaluationQuestion(BaseDocument):
    name = StringField(required=True, unique=True)
    abstract_search_result = DictField()
    bm25_cosine_similarity_result = DictField()
    bert_cosine_similarity_result = DictField()
    news_link_entities = ListField(StringField())
    news_link_result = DictField()
    newslink_bert_cosine_similarity_result = DictField()

    context_entities = ListField(StringField())
    kg_entities = ListField(StringField())
    popular_pattern = BooleanField()

    def extra_view(self):
        bm25_result = self.bm25_cosine_similarity_result.copy()
        bert_result = self.bert_cosine_similarity_result.copy()
        news_link_result = self.news_link_result.copy()
        abstract_search_result = self.abstract_search_result.copy()
        newslink_bert_result = self.newslink_bert_cosine_similarity_result.copy()
        bm25_result_ids = [item["id"][9:33] for item in bm25_result.get("docs", [])][
            0:5
        ]
        bert_result_ids = [item["id"][9:33] for item in bert_result.get("docs", [])][
            0:5
        ]
        news_link_ids = [item["id"] for item in news_link_result.get("docs", [])][0:5]
        newslink_bert_ids = [
            item["id"][9:33]
            for item in newslink_bert_result.get("docs", [])
            if item["id"] not in news_link_ids
        ][0:5]
        doc_ids = set(
            bm25_result_ids + bert_result_ids + news_link_ids + newslink_bert_ids
        )
        abstract_result_ids = [
            item["id"]
            for item in abstract_search_result.get("docs", [])
            if item["id"] not in doc_ids
        ]
        documents = NewsAnalytics.objects(id__in=abstract_result_ids + list(doc_ids))

        res = 'bm25<ul style="list-style-type:disc;">'
        for document in documents.filter(id__in=bm25_result_ids):
            res += f"<li>{document}</li>"
        res += "</ul>"

        res += 'BERT<ul style="list-style-type:disc;">'
        for document in documents.filter(id__in=bert_result_ids):
            res += f"<li>{document}</li>"
        res += "</ul>"

        res += 'NewsLink<ul style="list-style-type:disc;">'
        for document in documents.filter(id__in=news_link_ids):
            res += f"<li>{document}</li>"
        res += "</ul>"

        res += 'NewsLink-BERT<ul style="list-style-type:disc;">'
        for document in documents.filter(id__in=newslink_bert_ids):
            res += f"<li>{document}</li>"
        res += "</ul>"

        res += 'NCExplorer<ul style="list-style-type:disc;">'
        for document in documents.filter(id__in=abstract_result_ids):
            res += f"<li>{document}</li>"
        res += "</ul>"

        categories = [c.split(":")[-1].replace("_", " ") for c in self.name.split(",")]
        res += "</u>"

        return res


class DocumentPatternEvaluation(BaseDocument):
    meta = {
        "indexes": [
            "document_pattern",
        ]
    }
    evaluation_session = StringField()
    scores = DictField()
    documents = ListField(ReferenceField(NewsAnalytics))
    document_pattern = ReferenceField(DocumentPatternEvaluationQuestion)
