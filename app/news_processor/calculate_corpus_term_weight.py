import os
import string

from flask import current_app


class CorpusText:
    def __init__(self, limit=None):
        from app.models.news_analytics import NewsAnalytics

        self.count = 0
        self.queryset = NewsAnalytics.objects(text__ne=None).only("spacy_json")
        if limit:
            self.queryset = self.queryset.limit(limit)

    def __iter__(self):
        return self

    def __next__(self):  # Python 2: def next(self)
        self.count += 1
        res = next(self.queryset).spacy_json
        text = res["text"]
        lemma_text = text
        for token in res["tokens"]:
            if token["lemma"] != text[token["start"] : token["end"]]:
                lemma_text = lemma_text.replace(
                    text[token["start"] : token["end"]], token["lemma"]
                )
        return lemma_text


def generate_corpus_tf_idf_vocabulary():
    import pickle

    from sklearn.feature_extraction.text import TfidfVectorizer

    path = os.path.dirname(__file__)

    refresh = False
    if refresh:
        tf = TfidfVectorizer(
            analyzer="word",
            # ngram_range=(1, 5),
            stop_words="english",
            lowercase=True,
            max_features=500000,
        )

        corpus = CorpusText(limit=None)
        tfidf_vectors = tf.fit_transform(corpus)

        output = open(path + "/../../tfidf_vectors.pkl", "wb")
        pickle.dump(tfidf_vectors, output)
        output.close()
    else:
        pkl_file = open(path + "/../../tfidf_vectors.pkl", "rb")

        tfidf_vectors = pickle.load(pkl_file)

        pkl_file.close()
        src = path + "/../../news_analytics.pkl"
        tf = pickle.load(open(src, "rb"))

    import pandas as pd

    from app.models.news_analytics import NewsAnalytics

    feature_names = tf.get_feature_names()
    for idx, news in enumerate(NewsAnalytics.objects(text__ne=None)):
        vectors = tfidf_vectors[idx]
        df1 = pd.DataFrame(vectors.T.todense(), index=feature_names, columns=["tfidf"])
        df1 = df1.sort_values(by=["tfidf"], ascending=False)
        dense = vectors.todense()
        denselist = dense.tolist()
        tfidf_df = dict()
        for feature_name, dense_value in zip(feature_names, denselist[0]):
            if dense_value:
                tfidf_df[feature_name] = dense_value
        from app.models.document_entity import DocumentEntity

        prefix = current_app.config["DBPEDIA_PREFIX"]
        data = news.spacy_json
        for document_entity in DocumentEntity.objects(news_analytics=news.id):
            entity = document_entity.entity
            ents = [
                ent
                for ent in data.get("ents", [])
                if ent["params"].get("dbpedia_id")
                and ent["params"].get("dbpedia_id").split(prefix)[-1].replace(" ", "_")
                == entity
            ]
            if not ents:
                # try to find from alias
                from app.models.dbpedia_entity_alias import DBPediaEntityAlias

                alias = DBPediaEntityAlias.objects(subject=entity).first()
                if alias:
                    alias = alias.alias
                    ents = [
                        ent
                        for ent in data.get("ents", [])
                        if ent["params"].get("dbpedia_id")
                        and ent["params"]
                        .get("dbpedia_id")
                        .split(prefix)[-1]
                        .replace(" ", "_")
                        in alias
                    ]
            if not ents:
                continue
            ent = ents[0]
            entity_lemma = [item.lower() for item in ent["lemma"]]

            def _sanitize(entity_str):
                import re

                chars = re.escape(string.punctuation)
                return re.sub(r"[" + chars + "]", " ", entity_str)

            if _sanitize(entity_lemma[0]) in tfidf_df.keys():
                tfidf_key = _sanitize(entity_lemma[0])
            elif _sanitize(data["text"][ent["start"] : ent["end"]]) in tfidf_df.keys():
                tfidf_key = _sanitize(data["text"][ent["start"] : ent["end"]])
            elif _sanitize(entity.lower()) in tfidf_df.keys():
                tfidf_key = _sanitize(entity.lower())
            elif set(_sanitize(entity_lemma[0]).split(" ")).intersection(
                tfidf_df.keys()
            ):
                tfidf_key = (
                    set(_sanitize(entity_lemma[0]).split(" "))
                    .intersection(tfidf_df.keys())
                    .pop()
                )
            else:
                print(f"cannot find tfidf score for {entity_lemma}")
            score = tfidf_df.get(tfidf_key, 0)
            document_entity.tfidf_score = score
            document_entity.save()
