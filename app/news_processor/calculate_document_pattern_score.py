from mongoengine import Q

from app.models.document_entity_category import DocumentEntityCategory
from app.models.document_pattern import DocumentPattern, DocumentPatternProcessingState


def _calculate_document_pattern_relevance_score(document_pattern):
    print(document_pattern)
    categories = document_pattern.categories

    pipeline = [
        {
            "$match": {
                "category": {"$in": categories},
                "total_relevance_score": {"$gte": 0.5},
            },
        },
        {
            "$group": {
                "_id": "$news_analytics",
                "categories": {"$addToSet": "$category"},
                "entities": {
                    "$addToSet": "$entity"
                },  # abstraction need to map to different entity
                "relevance_scores": {"$push": "$total_relevance_score"},
            }
        },
        {
            "$project": {
                "_id": 1,
                "categories": 1,
                "entities": 1,
                "num_category": {"$size": "$categories"},
                "num_entity": {"$size": "$entities"},
                "total_relevance_score": {"$sum": "$relevance_scores"},
            }
        },
        {
            "$match": {
                "num_category": {"$eq": len(categories)},
                "num_entity": {"$gte": len(categories)},
            }
        },
    ]
    res = list(DocumentEntityCategory.objects.aggregate(pipeline))
    new_document_ids = set()
    total_relevance_score = 0
    for item in res:
        new_document_ids.add(item["_id"])
        total_relevance_score += item["total_relevance_score"]

    document_pattern.relevance_score = total_relevance_score
    document_pattern.documents = list(new_document_ids)
    document_pattern.document_count = len(document_pattern.documents)
    document_pattern.processing_state = (
        DocumentPatternProcessingState.DOCUMENTS_UPDATED.value
    )

    document_pattern.save()


def _calculate_document_pattern_diversity_score(document_pattern):
    print(document_pattern)
    categories = document_pattern.categories

    category_entity_map_kg = dict()

    from app.models.dbpedia_entity_category import DBPediaEntityCategory

    for item in DBPediaEntityCategory.objects(category__in=categories):
        category_entity_map_kg[item.category] = category_entity_map_kg.get(
            item.category, []
        )
        category_entity_map_kg[item.category].append(item.entity)

    pipeline = [
        {
            "$match": {
                "category": {"$in": categories},
                "news_analytics": {
                    "$in": [
                        item.id if hasattr(item, "id") else item
                        for item in document_pattern.documents
                    ]
                },
            },
        },
        {
            "$group": {
                "_id": "$category",
                "entities": {"$push": "$entity"},
            }
        },
        {
            "$project": {
                "_id": 1,
                "entities": 1,
            }
        },
    ]
    res = list(DocumentEntityCategory.objects.aggregate(pipeline))
    selected_entities = dict()
    for item in res:
        selected_entities[item["_id"]] = item["entities"]

    document_pattern.diversity_score = 0
    if res:
        diversity_scores = dict()
        for category, entities in selected_entities.items():
            max_possible_entities = min(
                len(category_entity_map_kg.get(category, [])),
                document_pattern.document_count,
            )
            if max_possible_entities:
                diversity_score = len(set(entities)) / max_possible_entities
                if diversity_score > 1:
                    diversity_score = len(set(entities)) / len(entities)
                diversity_scores[category] = diversity_score

        if diversity_scores:
            document_pattern.diversity_score = round(max(diversity_scores.values()), 3)
            document_pattern.diversity_scores = diversity_scores

    if document_pattern.document_count > 4:
        document_pattern.processing_state = (
            DocumentPatternProcessingState.SCORE_UPDATED.value
        )
    else:
        document_pattern.processing_state = (
            DocumentPatternProcessingState.EXPANDED.value
        )

    document_pattern.save()


def task_calculate_document_pattern_coverage_score(skip):
    from mongoengine import Q

    from app.models.document_pattern import (
        DocumentPattern,
        DocumentPatternProcessingState,
    )

    query = Q(processing_state=DocumentPatternProcessingState.DOCUMENTS_OUTDATED.value)

    queryset = (
        DocumentPattern.objects(query)
        .order_by("category_count")
        .skip(skip * 100)
        .limit(100)
    )

    while queryset:
        print(queryset.count())
        for pattern in queryset:
            _calculate_document_pattern_relevance_score(pattern)
            assert (
                pattern.processing_state
                == DocumentPatternProcessingState.DOCUMENTS_UPDATED.value
            )

        queryset = (
            DocumentPattern.objects(query)
            .order_by("category_count")
            .skip(skip * 100)
            .limit(100)
        )


def task_calculate_document_pattern_diversity_score(skip):
    from mongoengine import Q

    from app.models.document_pattern import (
        DocumentPattern,
        DocumentPatternProcessingState,
    )

    query = Q(processing_state=DocumentPatternProcessingState.DOCUMENTS_UPDATED.value)

    queryset = (
        DocumentPattern.objects(query)
        .order_by("category_count")
        .skip(skip * 100)
        .limit(100)
    )

    while queryset:
        print(queryset.count())
        for pattern in queryset:
            _calculate_document_pattern_diversity_score(pattern)
            assert (
                pattern.processing_state
                != DocumentPatternProcessingState.DOCUMENTS_UPDATED.value
            )

        queryset = (
            DocumentPattern.objects(query)
            .order_by("category_count")
            .skip(skip * 100)
            .limit(100)
        )


def task_calculate_document_pattern_subtopics(skip=0):
    from mongoengine import Q

    from app.models.document_pattern import (
        DocumentPattern,
        DocumentPatternProcessingState,
    )

    query = Q(processing_state=DocumentPatternProcessingState.SCORE_UPDATED.value)
    query &= Q(document_count__gt=4)

    queryset = DocumentPattern.objects(query).skip(skip * 100).limit(100)

    while queryset:
        print(queryset.count())
        for pattern in queryset:
            print(f"{pattern}, documents {pattern.document_count}")
            pattern = _calculate_document_pattern_subtopics(pattern)
            processing_state = pattern.processing_state
            assert (
                pattern.processing_state
                == DocumentPatternProcessingState.EXPANDED.value
            )

        queryset = DocumentPattern.objects(query).skip(skip * 100).limit(100)


def task_document_pattern_generation(skip):
    task_calculate_document_pattern_coverage_score(skip)

    query = Q(processing_state=DocumentPatternProcessingState.SCORE_UPDATED.value)
    query &= Q(document_count__gt=4)

    record = DocumentPattern.objects(query).skip(skip * 100).first()
    while record:
        print(record)
        print("task_calculate_document_pattern_coverage_score")
        task_calculate_document_pattern_coverage_score(skip)
        print("task_calculate_document_pattern_diversity_score")
        task_calculate_document_pattern_diversity_score(skip)
        print("task_calculate_document_pattern_subtopics")
        task_calculate_document_pattern_subtopics(skip)
        record = DocumentPattern.objects(query).skip(skip * 100).first()


def export_all_category_entities_to_txt_file():
    from app.models.dbpedia_category import DBPediaCategory
    from app.models.dbpedia_entity_alias import DBPediaEntityAlias

    categories = DBPediaCategory.objects(
        is_meta_category=False, entity_count__gt=5, entity_count__lt=50
    ).distinct("name")
    pipeline = [
        {
            "$match": {
                "category": {"$in": categories},
                "concept_relevance_score": {"$gt": 0.3},
            }
        },
        {
            "$group": {
                "_id": "$category",
                "entities": {"$addToSet": "$entity"},
            }
        },
    ]
    res = list(DocumentEntityCategory.objects.aggregate(pipeline))
    all_entities = []
    for item in res:
        all_entities += item["entities"]
        all_entities += [f"{e}." for e in item["entities"]]
    wikidata_id_queryset = DBPediaEntityAlias.objects(subject__in=all_entities).only(
        "subject", "wikidata_id", "alias"
    )
    abstraction_wikidata_id_map = dict()
    for item in wikidata_id_queryset:
        abstraction_wikidata_id_map[item.subject] = item.wikidata_id
        for alias in item.alias:
            abstraction_wikidata_id_map[alias] = item.wikidata_id

    lines = []
    for item in res:
        wikidata_ids = set()
        for entity in item["entities"]:
            wikidata_id = abstraction_wikidata_id_map.get(entity)
            if not wikidata_id:
                wikidata_id = abstraction_wikidata_id_map.get(f"{entity}.")
            if wikidata_id:
                wikidata_ids.add(wikidata_id)
        line = f"{item['_id']},{','.join(wikidata_ids)}\n"
        if len(wikidata_ids) > 3:
            lines.append(line)
    with open("pattern_entities_full.txt", "w") as f:
        for line in lines:
            f.write(line)


def export_pattern_to_txt_file():
    from app.models.dbpedia_entity_alias import DBPediaEntityAlias

    document_pattern_queryset = DocumentPattern.objects(
        Q(
            name__in=[
                "Category:Elections,Category:Female_heads_of_government",
                "Category:Energy_crops,Category:International_trade",
                "Category:Crops,Category:International_trade",
            ]
        )
        | Q(trending=True)
    ).no_dereference()
    with open("pattern_entities.txt", "w") as f:
        entities = []
        for document_pattern in document_pattern_queryset:
            for (
                document,
                mapping,
            ) in document_pattern.abstraction_entity_mappings.items():
                entities += mapping.values()

        entities = [item for subl in entities for item in subl]
        entities_with_dot = [f"{item}." for item in entities]
        queryset2 = DBPediaEntityAlias.objects(
            subject__in=entities + entities_with_dot,
        ).only("subject", "wikidata_id", "alias")
        abstraction_wikidata_id_map = dict()
        for item in queryset2:
            abstraction_wikidata_id_map[item.subject] = item.wikidata_id
            for alias in item.alias:
                abstraction_wikidata_id_map[alias] = item.wikidata_id

        for document_pattern in document_pattern_queryset:
            for abstraction in document_pattern.categories:
                wikidata_ids = set()

                for mapping in document_pattern.abstraction_entity_mappings.values():
                    if len(mapping) != len(document_pattern.categories):
                        continue
                    entities = mapping.get(abstraction)
                    for entity in entities:
                        wikidata_id = abstraction_wikidata_id_map.get(entity)
                        if not wikidata_id:
                            wikidata_id = abstraction_wikidata_id_map.get(f"{entity}.")
                        if wikidata_id:
                            wikidata_ids.add(wikidata_id)

                line = f"{document_pattern.name.replace(',', '|')},{abstraction},{','.join(wikidata_ids)}\n"
                print(len(wikidata_ids))
                if len(wikidata_ids) > 3:
                    f.write(line)


def export_common_entities_to_file():
    from app.models.dbpedia_entity_alias import DBPediaEntityAlias
    from app.models.document_entity import DocumentEntity

    entities = DocumentEntity.objects.distinct("entity")
    entities_with_dot = [f"{item}." for item in entities]
    queryset = DBPediaEntityAlias.objects(
        subject__in=entities + entities_with_dot,
        wikidata_id__ne=None,
        dbpedia_hypernyms="Company",
    ).only("wikidata_id", "subject", "dbpedia_hypernyms")
    with open("common_entities.txt", "w") as f:
        for line in queryset:
            f.write(f"{line.wikidata_id},{line.subject},{line.dbpedia_hypernyms}\n")


def _calculate_document_pattern_subtopics(document_pattern):
    from app.models.document_entity_category import DocumentEntityCategory

    categories = document_pattern.categories
    categories.sort()

    document_pattern = (
        DocumentPattern.objects(name=",".join(categories)).no_dereference().first()
    )
    documents = [item.id for item in document_pattern.documents]

    existing_categories = set()
    for existing_document_pattern in DocumentPattern.objects(
        categories__all=categories, category_count=len(categories) + 1
    ).only("categories"):
        existing_categories = existing_categories.union(
            existing_document_pattern.categories
        )

    entities_to_exclude = DocumentEntityCategory.objects(
        news_analytics__in=documents, category__in=document_pattern.categories
    ).distinct("entity")
    updates = {}
    pipeline = [
        {
            "$match": {
                "news_analytics": {"$in": documents},
                "total_relevance_score": {"$gte": 0.5},
                "category": {"$nin": list(existing_categories)},
                "entity": {"$nin": entities_to_exclude},
            }
        },
        {
            "$group": {
                "_id": "$category",
                "documents": {"$push": "$news_analytics"},
                "entities": {
                    "$push": "$entity"
                },  # abstraction need to map to different entity
                "relevance_scores": {"$push": "$total_relevance_score"},
            }
        },
        {
            "$project": {
                "_id": 1,
                "total_relevance_score": {"$sum": "$relevance_scores"},
                "categories": 1,
                "entities": 1,
                "documents": 1,
                "document_count": {"$size": "$documents"},
                "relevance_scores": 1,
            }
        },
        # {"$match": {"document_count": {"$gt": 1}}},
    ]

    res = list(DocumentEntityCategory.objects.aggregate(pipeline))
    for item in res:
        new_categories = document_pattern.categories + [item["_id"]]
        new_categories.sort()
        name = ",".join(new_categories)
        updates[name] = {
            "documents": item["documents"],
            "categories": new_categories,
            "name": name,
            "category_count": len(new_categories),
            "document_count": len(item["documents"]),
            "processing_state": DocumentPatternProcessingState.DOCUMENTS_UPDATED.value,
            "relevance_score": round(item["total_relevance_score"], 5),
        }

    if updates:
        res = DocumentPattern.upsert_many(list(updates.values()))
    document_pattern.processing_state = DocumentPatternProcessingState.EXPANDED.value
    processing_state = document_pattern.processing_state
    document_pattern.save()
    return document_pattern


def task_refresh_pattern_and_subtopics(document_patterns):
    children_patterns = []
    print(
        f"refresh_pattern_and_subtopics. category count {document_patterns[0].category_count}, pattern count {len(document_patterns)}"
    )

    for document_pattern in document_patterns:
        if (
            document_pattern.processing_state
            == DocumentPatternProcessingState.DOCUMENTS_OUTDATED.value
        ):
            _calculate_document_pattern_relevance_score(document_pattern)
        if (
            document_pattern.processing_state
            == DocumentPatternProcessingState.DOCUMENTS_UPDATED.value
        ):
            _calculate_document_pattern_diversity_score(document_pattern)
        if (
            document_pattern.processing_state
            == DocumentPatternProcessingState.SCORE_UPDATED.value
            and document_pattern.document_count > 4
        ):
            _calculate_document_pattern_subtopics(document_pattern)
        else:
            print(f"{document_pattern.processing_state}  {document_pattern}")

        """
        # iteratively check children (dfs)
        for child_document_pattern in DocumentPattern.objects(
            categories__all=document_pattern.categories,
            category_count=document_pattern.category_count + 1,
            processing_state__nin=[DocumentPatternProcessingState.EXPANDED.value],
        ):
            children_patterns.append(child_document_pattern)
        """
    if children_patterns:
        task_refresh_pattern_and_subtopics(children_patterns)
