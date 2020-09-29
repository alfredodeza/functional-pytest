import jenkins


def test_jenkins_is_an_empty_dict():
    connection = jenkins.Jenkins()
    assert connection() == {}


def test_jenkins_is_patched_still():
    connection = jenkins.Jenkins()
    assert connection.get_node_config() == """<?xml version="1.0" encoding="UTF-8"?><slave></slave>"""
