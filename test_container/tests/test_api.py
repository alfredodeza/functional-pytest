import requests


def test_success():
    response = requests.get('http://localhost:5000/')
    assert response.status_code == 200


def test_failure():
    response = requests.get('http://localhost:5000/error')
    assert response.status_code == 500


def test_os_release(client):
    result = client.run('flask_functional', ['cat', '/etc/os-release'])
    lines = result.split(b'\n')
    assert lines[0] == b'PRETTY_NAME="Debian GNU/Linux 10 (buster)"'
