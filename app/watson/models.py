from mongoengine import URLField, EmbeddedDocumentListField, EmbeddedDocument, FloatField, \
    StringField, ListField, EmbeddedDocumentField, ReferenceField, IntField, DictField

from app.common.mongoengine_base import BaseDocument


class Category(BaseDocument):
    label = StringField()

    def __unicode__(self):
        return self.label


class CategoryScore(EmbeddedDocument):
    score = FloatField(required=True)
    category = ReferenceField(Category, required=True)

    def __unicode__(self):
        return "%s %s" % (self.category, self.score)


class Concept(BaseDocument):
    '''
      {
      "text": "Lotus Software",
      "relevance": 0.839578,
      "dbpedia_resource": "http://dbpedia.org/resource/Lotus_Software"
    }
    '''
    text = StringField(required=True)
    url = URLField()


class ConceptScore(EmbeddedDocument):
    score = FloatField(required=True)
    concept = ReferenceField(Concept, required=True)


class Entity(BaseDocument):
    '''
        {
      "type": "Company",
      "text": "CNN",
      "sentiment": {
        "score": 0.0,
        "label": "neutral"
      },
      "relevance": 0.784947,
      "disambiguation": {
        "subtype": [
          "Broadcast",
          "AwardWinner",
          "RadioNetwork",
          "TVNetwork"
        ],
        "name": "CNN",
        "dbpedia_resource": "http://dbpedia.org/resource/CNN"
      },
      "count": 9
    }
    '''
    type = StringField(required=True)
    name = StringField(required=True)
    url = URLField()
    extra_data = DictField()
    subtypes = ListField(StringField())


class EntityScore(EmbeddedDocument):
    count = IntField()
    score = FloatField()
    entity = ReferenceField(Entity, required=True)


class Keyword(BaseDocument):
    '''
      {
      "text": "curated online courses",
      "sentiment": {
        "score": 0.792454
      },
      "relevance": 0.864624,
      "emotions": {
        "sadness": 0.188625,
        "joy": 0.522781,
        "fear": 0.12012,
        "disgust": 0.103212,
        "anger": 0.106669
      }
    }
    '''
    pass

class WatsonAnalytics(BaseDocument):
    url = URLField()
    categories = ListField(EmbeddedDocumentField(CategoryScore))
    entities = ListField(EmbeddedDocumentField(EntityScore))
    concepts = ListField(EmbeddedDocumentField(ConceptScore))
    keywords = DictField()
    sadness = FloatField()
    joy = FloatField()
    fear = FloatField()
    disgust = FloatField()
    anger = FloatField()
    sentiment_score = FloatField()