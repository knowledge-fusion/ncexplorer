from flask import current_app, json
from pymongo import UpdateOne
from watson_developer_cloud import NaturalLanguageUnderstandingV1
from watson_developer_cloud.natural_language_understanding_v1 import Features, EntitiesOptions, \
    KeywordsOptions, MetadataOptions, EmotionOptions, CategoriesOptions, ConceptsOptions, \
    RelationsOptions, SemanticRolesOptions, SentimentOptions, AnalysisResults

from app.finance_news.models import FinanceNews
from app.watson.models import Category, Entity, Concept, EntityScore, WatsonAnalytics, ConceptScore, \
    CategoryScore, Keyword, Author, SematicRole, Relation


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
        limit_text_characters=10000,
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
            relations=RelationsOptions(),
            semantic_roles=SemanticRolesOptions(limit=3),
            sentiment=SentimentOptions(),
        )
    )
    result = AnalysisResults._from_dict(response)
    operations = []
    for author in response['metadata']['authors']:
        name = author['name']
        operations.append(UpdateOne({'name': name}, {'$set': {'name': name}}, upsert=True))
    Author._get_collection().bulk_write(operations, ordered=False)

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

    document = WatsonAnalytics.objects(url=news.url).first()
    if not document:
        document = WatsonAnalytics(url=news.url)

    entities = [item['text'] for item in response['entities']]
    document.entities = []
    for item in Entity.objects(name__in=entities):
        entityScore = EntityScore(
            entity=item,
            score=find_attribute(response['entities'], 'text', item.name, 'relevance'),
            count=find_attribute(response['entities'], 'text', item.name, 'count')
        )
        document.entities.append(entityScore)

    concepts = [item['text'] for item in response['concepts']]
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
    for item in response['keywords']:
        keyword = Keyword(
            text=item['text'],
            sentiment_score=item['sentiment']['score'],
            score=item['relevance'],
            sadness=item['emotion']['sadness'],
            joy=item['emotion']['joy'],
            fear=item['emotion']['fear'],
            disgust=item['emotion']['disgust'],
            anger=item['emotion']['anger']
        )
        document.keywords.append(keyword)

    document.semantic_roles = []
    for item in response['semantic_roles']:
        sematicRole = SematicRole(
            action=item['action'],
            object=item['object'],
            subject=item['subject'],
            sentence=item['sentence']
        )
        document.semantic_roles.append(sematicRole)

    document.relations = []
    for item in response['relations']:
        relation = Relation(
            type=item['type'],
            score=item['score'],
            sentence=item['sentence'],
            arguments=item['arguments']
        )
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


def find_attribute(lst, key, value, attribute_key):
    for item in lst:
        if item[key] == value:
            return item[attribute_key]
