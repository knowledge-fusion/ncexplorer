from flask import current_app, json
from pymongo import UpdateOne
from watson_developer_cloud import NaturalLanguageUnderstandingV1
from watson_developer_cloud.natural_language_understanding_v1 import Features, EntitiesOptions, \
    KeywordsOptions, MetadataOptions, EmotionOptions, CategoriesOptions, ConceptsOptions, \
    RelationsOptions, SemanticRolesOptions, SentimentOptions

from app.finance_news.models import FinanceNews
from app.watson.models import Category, Entity, Concept, EntityScore, WatsonAnalytics


def analyze():
    natural_language_understanding = NaturalLanguageUnderstandingV1(
        username=current_app.config['WATSON_USERNAME'],
        password=current_app.config['WATSON_PASSWORD'],
        version=current_app.config['WATSON_VERSION']
    )

    news = FinanceNews.objects(id='5af15e508ea7681409c6fedb').first()

    response = natural_language_understanding.analyze(
        html=news.html,
        return_analyzed_text=True,
        clean=True,
        features=Features(
            entities=EntitiesOptions(
                emotion=True,
                sentiment=True,
                limit=5),
            keywords=KeywordsOptions(
                emotion=True,
                sentiment=True,
                limit=5),
            metadata=MetadataOptions(),
            emotion=EmotionOptions(),
            categories=CategoriesOptions(),
            concepts=ConceptsOptions(
                limit=3),
            # relations=RelationsOptions(),
            # semantic_roles=SemanticRolesOptions(),
            sentiment=SentimentOptions(),
        )
    )

    operations = []
    for category in response['categories']:
        '''
        {
            "score": 0.594296,
            "label": "/technology and computing/software"
        }
        '''
        label = category['label']
        operations.append(UpdateOne({"label": label}, {'$set': {"label": label}}, upsert=True))

    res = Category._get_collection().bulk_write(operations, ordered=False)

    operations = []

    for entity in response['entities']:
        if not entity.get('disambiguation', None):
            continue
        updates = {
            'type': entity['type'],
            'subtypes': entity['disambiguation']['subtype'],
            'name': entity['text']
        }
        if entity['text'] == entity['disambiguation']['name']:
            updates['url'] = entity['disambiguation']['dbpedia_resource']
        operations.append(UpdateOne({'name': entity['text']}, {'$set': updates}, upsert=True))
    res = Entity._get_collection().bulk_write(operations, ordered=False)

    operations = []
    for concept in response['concepts']:
        updates = {
            'url': concept['dbpedia_resource'],
            'text': concept['text']
        }
        operations.append(UpdateOne({'text': concept['text']}, {'$set': updates}, upsert=True))
    res = Concept._get_collection().bulk_write(operations, ordered=False)

    document = {
        'url': news.url,
        'entities': [],
        'categories': [],
        'concepts': [],
        'keywords': [],
    }
    entities = [item['text'] for item in response['entities']]
    for item in Entity.objects(name__in=entities):
        entity = EntityScore(
            entity=item,
            score=find_attribute(response['entities'], 'text', item.name, 'relevance'),
            count=find_attribute(response['entities'], 'text', item.name, 'count')
        )
        document['entities'].append(entity)

    #WatsonAnalytics.objects(url=news.url).upsert_one()
    print(json.dumps(response, indent=2))


def find_attribute(lst, key, value, attribute_key):
    for item in lst:
        if item[key] == value:
            return item[attribute_key]
