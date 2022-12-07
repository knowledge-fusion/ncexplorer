#!/usr/bin/env python
import datetime

from celery import group
from celery.signals import worker_ready
from celery_singleton import clear_locks

from app.application import celery
from app.models.utility_models import SyncStatus
from app.utils import chunks

# pylint: disable=invalid-name,unused-argument

logger = celery.log.get_default_logger()
celery.autodiscover_tasks(
    [
        "app.news_importer",
        "app.news_processor",
    ]
)


@celery.task(bind=True, name="tasks.test")
def test(self):
    logger.info("celery_beat_test")
    return True


###
# models
###


@celery.task(bind=True, name="tasks.stock_daily_timeseries_data_fetch_symbol")
def stock_daily_timeseries_data_fetch_symbol(self, symbols):
    for symbol in symbols:
        status = SyncStatus.objects(symbol=symbol, provider="alphavantage").first()
        try:
            from app.news_importer.stock_data_importer import fetch_daily_stock_data

            fetch_daily_stock_data(symbol, "full")
        except Exception as e:
            celery.logger.error(e, extra={"symbol": symbol})
        status.has_more = False
        status.save()
    return True


@celery.task(bind=True, name="tasks.stock_daily_timeseries_data")
def stock_daily_timeseries_data(self):
    queryset = SyncStatus.objects(has_more=True, provider="alphavantage").distinct(
        "symbol"
    )
    tasks = []
    for symbols in list(chunks(queryset, 10)):
        if len(tasks) > 10:
            break
        tasks.append(stock_daily_timeseries_data_fetch_symbol.s(symbols))
    return group(tasks)()


@celery.task(bind=True, name="tasks.update_counter_task")
def update_counter_task(self):
    logger.warn("update_counter_task")
    # for healthchecking to verify lambda scheduled events are functioning
    key = "task_scheduler_test_counter"

    from app.common.models import SystemConfig

    res = SystemConfig.update_timestamp_value(key)
    logger.warn("update_counter_task %s" % res.value)
    return True


@celery.task(
    bind=True,
    name="tasks.adhoc_task",
)
def adhoc_task(self, skip):
    logger.warn(f"adhoc_task_worker {skip}")
    from app.news_processor.adhoc_tasks import task_run_pipeline
    from app.services.slack_notification import send_slack_notification

    task_run_pipeline(skip)
    send_slack_notification(f"adhoc_task done {skip}")

    return True


@celery.task(bind=True, name="tasks.adhoc_task_master")
def adhoc_task_master(self):
    logger.warn("adhoc_task_coordinator")
    tasks = []
    now = datetime.datetime.utcnow()
    for idx in range(0, 4):
        tasks.append(adhoc_task.s(idx * 20))
    g = group(tasks)
    res = g()
    return res


###
# hooks
###


@celery.task
def error_handler(uuid):
    from celery.result import AsyncResult

    result = AsyncResult(uuid)
    exc = result.get(propagate=False)
    logger.error(f"Task {uuid} raised exception: {exc!r}\n{result.traceback!r}")


@worker_ready.connect
def unlock_all(**kwargs):
    clear_locks(celery)
