def test_dbpedia_specificity_score():
    from app.models.dbpedia_category import DBPediaCategory

    DBPediaCategory.calculate_specificity_score()


def test_calculate_kg_node_degree():
    from app.models.dbpedia_entity_alias import DBPediaEntityAlias

    res = DBPediaEntityAlias.get_kg_node_degrees(["Elon_Musk"])
    res
