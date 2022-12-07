import requests


def send_slack_notification(message):
    url = (
        "https://hooks.slack.com/services/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"
    )
    data = {"text": message}
    res = requests.post(url, json=data)
    pass
