import os

from flask import current_app
from pymongo import UpdateOne
from watson_developer_cloud import NaturalLanguageUnderstandingV1
from watson_developer_cloud.natural_language_understanding_v1 import Features, EntitiesOptions, \
    KeywordsOptions, MetadataOptions, EmotionOptions, CategoriesOptions, ConceptsOptions, \
    RelationsOptions, SemanticRolesOptions, SentimentOptions, AnalysisResults

from app.watson.models import Category, Entity, Concept, EntityScore, WatsonAnalytics, ConceptScore, \
    CategoryScore, Keyword, Author, SematicRole, Relation


def analyze(username, password, url, html):
    natural_language_understanding = NaturalLanguageUnderstandingV1(
        username=username,
        password=password,
        version=os.getenv('WATSON_VERSION')
    )
    query = {'html': html} if html else {'url': url}

    features = Features(
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
            relations=RelationsOptions(),
            semantic_roles=SemanticRolesOptions(limit=3),
            sentiment=SentimentOptions(),
        )

    response = natural_language_understanding.analyze(
        features,
        return_analyzed_text=True,
        clean=True,
        limit_text_characters=10000,
        **query
    )

    operations = []
    for author in response.get('metadata', {}).get('authors', []):
        name = author['name']
        operations.append(UpdateOne({'name': name}, {'$set': {'name': name}}, upsert=True))
    if operations:
        Author._get_collection().bulk_write(operations, ordered=False)

    operations = []
    for category in response.get('categories', []):
        '''
        {
            "score": 0.594296,
            "label": "/technology and computing/software"
        }
        '''
        label = category['label']
        operations.append(UpdateOne({"label": label}, {'$set': {"label": label}}, upsert=True))
    if operations:
        res = Category._get_collection().bulk_write(operations, ordered=False)

    operations = []
    for entity in response.get('entities', []):
        if not entity.get('disambiguation', None):
            continue
        updates = {
            'type': entity['type'],
            'subtypes': entity['disambiguation']['subtype'],
            'name': entity['text']
        }
        if entity['text'] == entity['disambiguation'].get('name', ''):
            updates['url'] = entity['disambiguation']['dbpedia_resource']
        operations.append(UpdateOne({'name': entity['text']}, {'$set': updates}, upsert=True))
    if operations:
        res = Entity._get_collection().bulk_write(operations, ordered=False)

    operations = []
    for concept in response.get('concepts', []):
        updates = {
            'url': concept['dbpedia_resource'],
            'text': concept['text']
        }
        operations.append(UpdateOne({'text': concept['text']}, {'$set': updates}, upsert=True))
    if operations:
        res = Concept._get_collection().bulk_write(operations, ordered=False)

    document = WatsonAnalytics.objects(url=url).first()
    if not document:
        document = WatsonAnalytics(url=url)

    entities = [item['text'] for item in response.get('entities', [])]
    document.entities = []
    for item in Entity.objects(name__in=entities):
        entityScore = EntityScore(
            entity=item,
            score=find_attribute(response['entities'], 'text', item.name, 'relevance'),
            count=find_attribute(response['entities'], 'text', item.name, 'count')
        )
        document.entities.append(entityScore)

    concepts = [item['text'] for item in response.get('concepts', [])]
    document.concepts = []
    for item in Concept.objects(text__in=concepts):
        conceptScore = ConceptScore(
            concept=item,
            score=find_attribute(response['concepts'], 'text', item.text, 'relevance')
        )
        document.concepts.append(conceptScore)

    categories = [item['label'] for item in response['categories']]
    document.categories = []
    for item in Category.objects(label__in=categories):
        categoryScore = CategoryScore(
            category=item,
            score=find_attribute(response['categories'], 'label', item.label, 'score')

        )
        document.categories.append(categoryScore)

    authors = [item['name'] for item in response['metadata']['authors']]
    document.authors = Author.objects(name__in=authors).only('id')

    document.keywords = []
    for item in response.get('keywords', []):
        keyword = Keyword(
            text=item['text'],
            sentiment_score=item['sentiment']['score'],
            score=item['relevance'],
        )
        if item.get('emotion', None):
            keyword.sadness = item['emotion']['sadness']
            keyword.joy = item['emotion']['joy']
            keyword.fear = item['emotion']['fear']
            keyword.disgust = item['emotion']['disgust']
            keyword.anger = item['emotion']['anger']
        document.keywords.append(keyword)

    document.semantic_roles = []
    for item in response.get('semantic_roles',[]):
        sematicRole = SematicRole(
            action=item['action'],
            object=item.get('object'),
            subject=item['subject'],
            sentence=item['sentence']
        )
        document.semantic_roles.append(sematicRole)

    document.relations = []
    for item in response.get('relations', []):
        relation = Relation(
            type=item['type'],
            score=item['score'],
            sentence=item['sentence'],
        )
        if item['arguments']:
            relation.arguments1 = item['arguments'][0]
        if len(item['arguments']) > 1:
            relation.arguments2 = item['arguments'][1]

        document.relations.append(relation)

    emotion = response['emotion']['document']['emotion']
    document.sadness = emotion['sadness']
    document.joy = emotion['joy']
    document.fear = emotion['fear']
    document.disgust = emotion['disgust']
    document.anger = emotion['anger']
    document.sentiment_score = response['sentiment']['document']['score']
    document.title = response['metadata']['title']
    document.analyzed_text = response['analyzed_text']
    document.publication_date = response['metadata']['publication_date']

    document.save()

    return True


def find_attribute(lst, key, value, attribute_key):
    for item in lst:
        if item[key] == value:
            return item[attribute_key]
