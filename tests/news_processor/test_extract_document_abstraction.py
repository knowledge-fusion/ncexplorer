def test_extract_document_abstraction():
    from app.news_processor.extract_document_entity_abstraction import (
        _extract_document_entity_abstraction,
    )

    url = "  https://seekingalpha.com/news/3352374-amazon-halts-seattle-building-awaiting-council-tax-vote "
    url = "https://www.npr.org/sections/thetwo-way/2016/05/09/477423367/more-journalists-leaving-las-vegas-review-journal-after-sale-to-billionaire"
    _extract_document_entity_abstraction(url.strip())
    pass
