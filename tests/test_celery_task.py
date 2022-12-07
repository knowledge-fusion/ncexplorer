def test_adhoc_task_main(celery_app):
    from app.tasks import adhoc_task_master

    res = adhoc_task_master.delay().get()
    assert res.successful()


def test_adhoc_task():
    from app.tasks import adhoc_task

    adhoc_task(0)


def test_data_migration():
    from app.commandline import data_migration

    data_migration()


def test_data_cleaning():
    from app.news_processor.adhoc_tasks import task_data_cleaning

    task_data_cleaning()
