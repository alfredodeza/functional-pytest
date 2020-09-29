import jenkins


def test_jenkins_is_patched():
    connection = jenkins.Jenkins()
    assert connection.get_node_config() == """<?xml version="1.0" encoding="UTF-8"?><slave></slave>"""
