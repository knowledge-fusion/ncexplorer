import os

from flask import current_app, render_template_string, render_template

from app.config import DefaultConfig
from app.extenstions import cache


def get_config(key):
    result = None
    try:
        result = current_app.config.get(key)
    except RuntimeError:
        result = getattr(DefaultConfig, key)
    return result


@cache.memoize(timeout=None)
def get_remote_template(url):
    import requests
    try:
        resp = requests.get(url)
        return resp.text if resp.status_code == 200 else None
    except Exception as e:
        return None


def render(source, **context):
    remote_base_url = current_app.config.get("REMOTE_TEMPLATE_BASE_URL", None)
    template_string = None
    if remote_base_url:
        template_string = get_remote_template(remote_base_url + source)

    if template_string:
        response = render_template_string(template_string, **context)
    else:
        response = render_template(source, **context)
    return response


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
