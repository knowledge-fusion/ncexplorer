def test_related_term():
    from app.views.pattern_explore import related_term

    related_term("Tesla")


def test_pattern_entities():
    from app.views.pattern_explore import pattern_entities

    pattern_entities(
        "Category:Companies_listed_on_the_Nasdaq,Category:English-speaking_countries_and_territories"
    )


def test_search_abstraction():
    from app.views.pattern_explore import search_abstraction

    search_abstraction("ukra")


def test_search_entity():
    from app.views.pattern_explore import search_entity

    search_entity("tesla")


def test_get_documents_with_patterns():
    from app.views.pattern_explore import get_documents_with_patterns

    pattern = "Category:Mergers_and_acquisitions,Category:Software_companies_of_the_United_States"
    pattern = "Category:Electric_motor_manufacturers"
    documents = get_documents_with_patterns(
        # "Category:International_trade,Category:Crops,Category:Staple_foods",
        pattern,
        # frecord.name,
        1,
        5,
    )
    from app.views.pattern_explore import related_term

    res = related_term(pattern)
    res


def test_load_random_pattern():
    from app.views.pattern_explore import load_random_pattern

    load_random_pattern()


def test_get_sentiment(app):
    from app.news_processor.calculate_document_sentiment_score import (
        task_batch_calculate_document_sentiment_score,
    )

    task_batch_calculate_document_sentiment_score()


def test_pattern_relevance_survey_questions(app):
    with app.test_client() as versioned_user_agent:
        url = "/pattern_relevance_survey_questions/Category:Lawsuits,Category:Software_companies_of_the_United_States"
        resp = versioned_user_agent.get(url)
        data = resp.json
        data


def test_answer_pattern_relevance_survey(app):
    with app.test_client() as versioned_user_agent:
        url = "/answer_pattern_relevance_survey"
        data = {
            "answers": {"5eeaaa09f97761a2e1d3599a": 1},
            "pattern_name": "Category:Biotechnology_companies_of_the_United_States,Category:Corporate_finance",
            "evaluation_session": "127.0.0.1-2022-01-07 10:02:24.611421",
        }
        resp = versioned_user_agent.post(url, json=data)
        data = resp.json
        data
