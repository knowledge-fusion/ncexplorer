def test_abstraction_document_relevance_score():
    url = "https://seekingalpha.com/news/1549981-reports-google-to-make-ad-product-chief-youtube-ceo"
    # url = "https://seekingalpha.com/news/3345047-monsanto-patent-bt-cotton-india-court-rules"
    url = "http://read.bi/16vRjB3"

    from app.models.news_analytics import NewsAnalytics

    news_analytics = NewsAnalytics.objects(url=url).first()
    from app.news_processor.calculate_document_entity_abstraction_score import (
        _document_entity_abstraction_score,
    )

    _document_entity_abstraction_score(news_analytics=news_analytics)


def test_get_entities_paths():
    from app.news_processor.calculate_document_entity_abstraction_score import (
        get_entities_paths,
    )

    entity1 = "Country"
    entity2 = "JL_Darling"
    paths = get_entities_paths(entity1=entity1, entity2=entity2, force_refresh=True)
    paths.save()


def test_abstraction_kg_paths_context_entities():
    from app.news_processor.calculate_document_entity_abstraction_score import (
        calculate_concept_relevance_scores,
    )

    context_entities = [
        "Iran",
        "Election",
        #  "Slate",
        #  "Parliamentary_system",
        #  "Supporter",
        #  "Candidate",
    ]

    for category, entity in [
        ("Category:Building_stone", "Slate"),
        ("Category:Islamic_republics", "Iran"),
        ("Category:Former_monarchies_of_Western_Asia", "Iran"),
    ]:
        score, duration = calculate_concept_relevance_scores(
            category, context_entities=context_entities
        )

        print(f"{category}, {entity}, {score} {duration}")
