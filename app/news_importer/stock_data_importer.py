import os
from datetime import datetime

from pymongo import UpdateOne

from app.models.stock_data_models import StockDailyTimeSeries
from app.utils import graceful_auto_reconnect


@graceful_auto_reconnect
def save_stock_data(operations):
    res = False
    if operations:
        res = StockDailyTimeSeries._get_collection().bulk_write(
            operations, ordered=False
        )
    return res


# pylint: disable=unbalanced-tuple-unpacking,invalid-sequence-index
def fetch_daily_stock_data(symbol, outputsize):
    from alpha_vantage.timeseries import TimeSeries

    key = str(os.getenv("ALPHAVANTAGE_API_KEY"))
    time_series = TimeSeries(key=key, output_format="json")
    data, meta_data = time_series.get_daily_adjusted(
        symbol=symbol, outputsize=outputsize
    )
    assert symbol == meta_data["2. Symbol"]
    operations = []
    for date, item in data.items():
        date = datetime.strptime(date, "%Y-%m-%d")
        updates = {
            "symbol": symbol,
            "date": date,
            "open": float(item["1. open"]),
            "high": float(item["2. high"]),
            "low": float(item["3. low"]),
            "close": float(item["4. close"]),
            "adjusted_close": float(item["5. adjusted close"]),
            "volume": int(item["6. volume"]),
            "dividend_amount": float(item["7. dividend amount"]),
            "split_coefficient": float(item["8. split coefficient"]),
            "delta": 0,
        }
        if updates["open"] > 0:
            updates["delta"] = (
                (updates["close"] - updates["open"]) / updates["open"] * 100
            )
        operations.append(
            UpdateOne({"symbol": symbol, "date": date}, {"$set": updates}, upsert=True)
        )
    res = save_stock_data(operations)
    return res


def calculate_daily_stock_delta():
    has_more = True
    while has_more:
        queryset = StockDailyTimeSeries.objects(delta=None).limit(10000)
        operations = []
        for entity in queryset:
            delta = 0
            if entity.open > 0:
                delta = (entity.close - entity.open) / entity.open * 100
            operations.append(
                {"delta": delta, "updated_at": datetime.utcnow(), "_id": entity.id}
            )
        if operations:
            StockDailyTimeSeries.update_many(operations)
            has_more = True
        else:
            has_more = False
