import json

from flask import current_app, flash, request, url_for
from flask_admin import AdminIndexView, expose
from flask_login import login_required


class ManualCronView(AdminIndexView):
    PURGE_TASKS = "purge_all_tasks"

    @login_required
    def is_accessible(self):
        return True

    def registered_tasks(self, celery):
        inspect = celery.control.inspect()
        tasks = []

        try:
            registered = inspect.registered()
            if registered:
                from itertools import chain

                tasks = set(chain.from_iterable(registered.values()))
                tasks = list(map(lambda task: task.split(" ")[0], tasks))
        except Exception as exp:
            current_app.logger.exception(exp)
        tasks.append(self.PURGE_TASKS)
        return sorted(tasks)

    @expose("/", methods=["GET", "POST"])
    def index(self):
        from app.tasks import celery

        tasks = []
        try:
            current_app.redis.ping()
            tasks = self.registered_tasks(celery)
        except Exception:
            pass

        task_url = None
        if request.method == "POST":
            task = request.form["action"]
            args = []
            if request.form["args"]:
                args = json.loads(request.form["args"])
            result = celery.send_task(task, args=args)
            flash(f"sent task, name {task}, args {args}, id {result.id}")
            task_url = url_for("task_status", task_id=result.id)
        res = self.render(
            "admin/manual_cron.html",
            tasks=tasks,
            task_url=task_url,
        )
        return res
