import os
from datetime import datetime

from pymongo import UpdateOne

from app.stock.models import StockDailyTimeSeries


def fetch_daily_stock_data(symbol, outputsize):
    from alpha_vantage.timeseries import TimeSeries
    ts = TimeSeries(key=os.getenv('ALPHA_VANTAGE'), output_format='json')
    data, meta_data = ts.get_daily_adjusted(symbol=symbol, outputsize=outputsize)
    assert symbol == meta_data['2. Symbol']
    operations = []
    for date, item in data.iteritems():
        date = datetime.strptime(date, '%Y-%m-%d')
        updates = {
            'symbol': symbol,
            'date': date,
            'open': float(item['1. open']),
            'high': float(item['2. high']),
            'low': float(item['3. low']),
            'close': float(item['4. close']),
            'adjusted_close': float(item['5. adjusted close']),
            'volume': int(item['6. volume']),
            'dividend_amount': float(item['7. dividend amount']),
            'split_coefficient': float(item['8. split coefficient'])
        }
        operations.append(UpdateOne({'symbol': symbol, 'date': date}, {'$set': updates},
                                    upsert=True))
    StockDailyTimeSeries._get_collection().bulk_write(operations, ordered=False)
