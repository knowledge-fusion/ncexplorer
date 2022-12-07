def test_import_outstaing_fact():
    from app.models.outstanding_fact import OutstandingFact

    OutstandingFact.import_facts()


def test_fill_entity():
    from app.models.outstanding_fact import OutstandingFact

    OutstandingFact.fill_entity()
