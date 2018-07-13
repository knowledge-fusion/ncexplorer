

def test_fetch_stock_daily_timeseries(celery_app, app, mock_alphavantage):
    from app.tasks import stock_daily_timeseries_data
    stock_daily_timeseries_data()


def parse_market_cap(string):
    res = None
    if string[-1] == 'M':
        res = float(string[1:-1])
    elif string[-1] == 'B':
        res = float(string[1:-1]) * 1000
    return res


def test_insert_stock(app):
    from app.finance_news.models import Stock
    from pymongo import UpdateOne

    operations = []
    with open('./data/nyse.csv') as csvfile:
        import csv
        reader = csv.DictReader(csvfile)
        reader.next()
        for row in reader:
            operations.append(UpdateOne(
                {'symbol': row['Symbol']},
                {'$set': {
                    'symbol': row['Symbol'],
                    'name': row['Name'],
                    'sector': row['Sector'],
                    'industry': row['industry'],
                    'ipo_year': int(row['IPOyear']) if row['IPOyear'].isdigit() else None,
                    'market_cap': parse_market_cap(row['MarketCap'])
                }},
                upsert=True))
    Stock._get_collection().bulk_write(operations, ordered=False)


def test_create_sync_status(app):
    from app.finance_news.models import Stock
    from pymongo import UpdateOne
    from app.finance_news.models import SyncStatus

    snp = []
    operations = []
    SyncStatus.objects(provider='alphavantage').delete()
    with open('./data/snp500.csv') as csvfile:
        import csv
        reader = csv.DictReader(csvfile)
        reader.next()
        for row in reader:
            snp.append(row['symbol'])

    stocks = Stock.objects.distinct('symbol')
    invalid = []
    for symbol in stocks:
        if not any(char.isdigit() for char in symbol):
            operations.append(UpdateOne(
                {'symbol': symbol},
                {'$set': {
                    'symbol': symbol,
                    'publisher': 'stock_data',
                    'provider': 'alphavantage',
                    'has_more': symbol in snp
                }},
                upsert=True))
        else:
            invalid.append(symbol)
    SyncStatus._get_collection().bulk_write(operations, ordered=False)
