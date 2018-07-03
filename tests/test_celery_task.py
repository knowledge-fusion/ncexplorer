

def test_watson_analytics(celery_app, app):
    from app.tasks import watson_analytics
    watson_analytics()