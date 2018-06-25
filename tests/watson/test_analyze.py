from app.watson.analyze import analyze


def test_natual_language_understanding(app):
    res = analyze(url='https://seekingalpha.com/news/3352333-accenture-sap-team-security-defense-security-agencies')