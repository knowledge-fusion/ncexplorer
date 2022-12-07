def test_print_hypernym():
    from app.models.dbpedia_entity_alias import DBPediaEntityAlias

    DBPediaEntityAlias.print_hypernym_count()
