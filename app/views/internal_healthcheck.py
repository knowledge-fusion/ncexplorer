def check_s3_data_backup_ok():
    import datetime

    import boto3
    from flask import current_app

    app = current_app
    session = boto3.Session()

    # Then use the session to get the resource
    s3 = session.resource("s3")

    data_backup_bucket = s3.Bucket(app.config["DATA_BACKUP_BUCKET"])
    keys = []
    for my_bucket_object in data_backup_bucket.objects.all():
        keys.append(my_bucket_object.key)
    print(keys)
    yesterday = datetime.datetime.utcnow() - datetime.timedelta(days=1)
    fmt = "%d%b%Y"
    key = f"{yesterday.strftime(fmt)}/finance/news_analytics.bson.gz"
    backup_success = key in keys
    print(key)
    print(backup_success)
    return backup_success, "ok"


def cron_task_scheduler_status_ok():
    import datetime

    from app.common.models import SystemConfig

    key = "task_scheduler_test_counter"
    last_execute = SystemConfig.get_or_create_timestamp_value(key)
    delta = datetime.datetime.utcnow() - last_execute
    if delta.total_seconds() > 15 * 60:
        return (
            False,
            "task_scheduler_test_counter last update is {} minutes ago".format(
                delta.total_seconds() / 60
            ),
        )

    return True, "ok"


def mongo_available():
    from flask import current_app
    from pymongo import MongoClient

    try:
        host = current_app.config["MONGO_MONITORING_HOST"]
        client = MongoClient(host)
        msg = ""
        result = True
        if "rs" in host:
            members = []
            res = client.admin.command("replSetGetStatus")["members"]
            for item in res:
                member = dict()
                for key in ["health", "state", "stateStr", "uptime"]:
                    member[key] = item[key]
                if not member["health"] or member["stateStr"] not in [
                    "PRIMARY",
                    "SECONDARY",
                ]:
                    res = False
                members.append(member)
            msg = members
        else:
            info = client.server_info()
            msg = {"ok": info["ok"], "version": info["version"]}
        return result, msg
    except Exception as e:
        return False, "%s" % e
