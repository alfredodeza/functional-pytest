import requests


def test_success():
    response = requests.get('http://localhost:5000/')
    assert response.status_code == 201


def test_failure():
    response = requests.get('http://localhost:5000/error')
    assert response.status_code == 500
