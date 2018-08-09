from flask import flash
from flask import request
from flask import url_for
from flask_admin import AdminIndexView, expose
from flask_login import login_required
from jinja2 import TemplateNotFound


class ManualCronView(AdminIndexView):
    @login_required
    def is_accessible(self):
        return True

    @expose('/', methods=['GET', 'POST'])
    def index(self):
        from app.tasks import celery
        tasks = celery.tasks.keys()
        tasks = [x for x in tasks if x.startswith('tasks.')]
        tasks.sort()
        task_url = None
        if request.method == 'POST':

            task = request.form['action']
            args = []
            if request.form['args']:
                args = request.form['args'].split(",")
            result = celery.send_task(task, args=args)
            flash("sent task, name %s, args %s, id %s" % (task, args, result.id))
            task_url = url_for('task_status', task_id=result.id)
        try:
            res = self.render('admin/manual_cron.html', tasks=tasks, task_url=task_url)
        except TemplateNotFound:
            res = super(ManualCronView, self).index()
        return res
