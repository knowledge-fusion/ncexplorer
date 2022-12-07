#!/usr/bin/env python

import click

# pylint: disable=unused-argument,unused-variable
from app.services.slack_notification import send_slack_notification


def upper(ctx, param, value):
    if value is not None:
        return value.upper()
    return value


def configure_commandline(app):
    @app.cli.command("hello")
    @click.option("--name", default="World", callback=upper)
    def hello_command(name):
        # flask hello
        click.echo(f"Hello, {name}!")

    @app.cli.command("urls")
    def urls():
        print("urls on app:")
        for rule in app.url_map.iter_rules():
            if rule.endpoint != "static" and rule.rule.find("/admin/") < 0:
                print(f"{rule.endpoint}  =>  {rule.rule}")

    @app.cli.command("data_migration")
    def data_migration_cli():
        # flask date_migration
        res = data_migration()
        print(res)


def data_migration():
    # pylint: disable=invalid-name,unused-import
    res = ["ok"]

    from flask import current_app

    try:

        from pymongo.errors import AutoReconnect

        try:
            from app.models.document_entity import DocumentEntity
            from app.models.document_entity_category import DocumentEntityCategory

            item = DocumentEntityCategory.objects(
                total_relevance_score=None, concept_relevance_score__gt=0
            ).first()
            while item:
                document_entities = DocumentEntity.objects(
                    news_analytics=item.news_analytics.id
                )
                document_categories = DocumentEntityCategory.objects(
                    news_analytics=item.news_analytics.id,
                    total_relevance_score=None,
                    concept_relevance_score__gt=0,
                )
                for entity in document_entities:
                    entity_score = entity.entity_tfidf_score
                    for category in document_categories.filter(entity=entity.entity):
                        category.total_relevance_score = (
                            entity_score * category.concept_relevance_score
                        )
                        category.save()
                print(item)
                item = DocumentEntityCategory.objects(
                    total_relevance_score=None, concept_relevance_score__gt=0
                ).first()

            from app.news_processor.adhoc_tasks import task_run_pipeline

            task_run_pipeline(0)

        except AutoReconnect as e:
            from time import sleep

            print("AutoReconnect")
            sleep(10)
            current_app.logger.error(e, exc_info=True)

    except Exception as e:

        current_app.logger.error(e, exc_info=True)
        res.append("%s" % e)
    from flask import current_app

    if not (current_app.config["DEBUG"] or current_app.config["TESTING"]):
        send_slack_notification("task_named_entity_linking done")

    return ",".join(res)
