def test_task_calculate_document_abstraction_similar_news():
    from app.news_processor.register_document_seed_patterns import (
        task_register_document_seed_patterns,
    )

    task_register_document_seed_patterns()


def test_calculate_document_abstraction_patterns():
    from app.news_processor.register_document_seed_patterns import (
        _register_document_seed_patterns,
    )

    url = "https://seekingalpha.com/news/3219205-googles-daydream-view-headset-available-next-thursday"
    # url = (
    #    "	https://seekingalpha.com/news/3347038-e-trade-minus-2_6-percent-big-quarter	"
    # )
    # url = "20150302-201412000-nL1N0W41SO-1-2"

    _register_document_seed_patterns(url.strip())
