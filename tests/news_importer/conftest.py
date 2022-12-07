import json
import os
from os.path import isfile, join

import pytest
import responses


def mock_endpoints():
    path = os.path.dirname(os.path.realpath(__file__)) + "/data/news_api"
    files = [f for f in os.listdir(path) if isfile(join(path, f))]
    res = dict()
    for f in files:
        if f != ".DS_Store":
            url = f.replace("-", "/")
            res[url] = f"{path}/{f}"
    return res


@pytest.fixture
def mock_news_api():
    endpoint_dict = mock_endpoints()

    for url in endpoint_dict.keys():
        filename = endpoint_dict[url]
        with open(filename) as f:
            response = json.load(f)
            responses.add(responses.GET, url, json=response)
