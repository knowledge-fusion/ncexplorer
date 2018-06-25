from app.admin.base import AuthModelView


class WatsonAnalyticsView(AuthModelView):
    column_exclude_list = ['extra_data', 'created_at', 'updated_at', 'url', 'analyzed_text']
