import json
import pytest

from app import app as flask_app


@pytest.fixture
def client():
    flask_app.testing = True
    with flask_app.test_client() as c:
        yield c


def post_analyze(client, text):
    rv = client.post('/analyze', json={'text': text})
    assert rv.status_code == 200
    return rv.get_json()


def test_analyze_stressed(client):
    out = post_analyze(client, 'I am really stressed and overwhelmed today')
    assert out['emotion'] in ('stressed', 'anxious') or 'stress' in out['keywords']
    assert 'reflection' in out and isinstance(out['reflection'], str)
    assert isinstance(out['stress'], int)


def test_analyze_calm(client):
    out = post_analyze(client, 'I feel calm and relaxed after my walk')
    assert out['emotion'] == 'calm'
    assert 'calm' in out['keywords'] or out['emotion'] == 'calm'


def test_analyze_happy(client):
    out = post_analyze(client, 'I am happy and excited about the good news')
    assert out['emotion'] == 'happy'
    assert 'happy' in out['keywords'] or 'joy' in out['keywords']
