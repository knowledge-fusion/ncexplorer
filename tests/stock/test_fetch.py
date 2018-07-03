import responses


def test_fetch_stock_daily_timeseries(celery_app, app, mock_alphavantage):
    from app.tasks import stock_daily_timeseries_data_fetch_symbol
    responses.start()
    stock_daily_timeseries_data_fetch_symbol('MSFT')
    responses.stop()