import json

import pytest
import responses
from os.path import isfile, join, dirname, realpath
import os




@pytest.fixture
def mock_alphavantage():
    filename = os.path.dirname(os.path.realpath(__file__)) + '/daily_timeseries.json'
    with open(filename) as f:
        response = json.load(f)
        url = 'http://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol=AAPL&outputsize=full&apikey=856Y8QXAUWN6MAWS&datatype=json'
        responses.add(responses.GET,
                      url,
                      json=response,
                      content_type="application/json")
