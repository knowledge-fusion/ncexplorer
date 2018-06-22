import os

from flask import current_app

from app.config import DefaultConfig


def get_config(key):
    result = None
    try:
        result = current_app.config.get(key)
    except RuntimeError:
        result = getattr(DefaultConfig, key)
    return result



def cache_api_response(backend, end_point, content):
    if get_config('CACHE_API_RESPONSE'):
        import responses
        mock_disabled = hasattr(responses.mock, '_patcher') \
                        and len(responses.mock._patcher._active_patches)

        if mock_disabled:
            basepath = os.path.dirname(__file__)
            path = current_app.config['API_RESPONSE_CACHE_DIR'] % (backend, end_point)
            filepath = os.path.abspath(os.path.join(basepath, path))
            f = open(filepath, 'w')
            f.write(content)
            f.close()