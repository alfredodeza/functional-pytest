from utils import ExitCode, create_client
import os
from os.path import dirname as _dir
import logging

import docker
from docker.errors import DockerException


def get_logger(name):
    return logging.getLogger('conftest.%s' % name)


def pytest_sessionstart(session):
    BASE_FORMAT = "[%(name)s][%(levelname)-6s] %(message)s"
    FILE_FORMAT = "[%(asctime)s]" + BASE_FORMAT

    root_logger = logging.getLogger('conftest')
    dir_path = os.path.dirname(os.path.realpath(__file__))
    top_level = _dir(_dir(dir_path))
    log_file = os.path.join(top_level, 'pytest-functional-tests.log')

    root_logger.setLevel(logging.DEBUG)

    # File Logger
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(FILE_FORMAT, "%Y-%m-%d %H:%M:%S"))

    root_logger.addHandler(fh)


def pytest_assertrepr_compare(op, left, right):
    if isinstance(left, ExitCode) and isinstance(right, ExitCode):
        return [
            "failure ExitCode(%s) %s ExitCode(%s)" % (left, op, right),
            "Exit status assertion failure, stdout and stderr context:",
            ] + [
            '   stdout: %s' % line for line in left.stdout.split('\n')
            ] + [
            '   stderr: %s' % line for line in left.stderr.split('\n')
        ]


def pytest_addoption(parser):
    """
    Do not Keep the container around and remove it after a test run. Useful
    only for the CI. When running locally a developer will probably want to
    keep the container around for easier/faster testing.
    """
    parser.addoption(
        "--nokeepalive", action="store_true",
        default=False, help="Do not keep docker container alive"
    )


def pytest_report_header(config):
    logger = get_logger('report_header')
    msg = []
    try:
        client = create_client()
        metadata = client.api.inspect_container('flask_functional')
    except docker.errors.NotFound:
        logger.info("No running container was found, can't add info to report header")
        metadata = {'Config': {}}
        msg = ['Docker: container not running yet']
    except DockerException as e:
        logger.exception('Unable to connect to a docker socket')
        msg = ['Docker: Unable to connect to a docker socket']
        msg.append('Error: %s' % str(e))
        return msg
    config = metadata['Config']
    #labels = config.get('Labels', {})

    msg.extend([
       #'   %s: %s' % (k, v) for k, v in labels.items()
       '    DOCKER>> %s: %s' % (k, v) for k, v in config.items()
    ])

    return msg


def pytest_runtest_logreport(report):
    if report.failed:
        client = create_client()

        test_containers = client.containers.list(
            all=True,
            filters={"name": "flask_functional"})
        for container in test_containers:
            # XXX magical number! get the last 10 log lines
            log_lines = [
                ("Container ID: {!r}:".format(container.attrs['Id'])),
                ] + container.logs().decode('utf-8').split('\n')[-10:]
            try:
                report.longrepr.addsection('docker logs', os.linesep.join(log_lines))
            except AttributeError:
                pass
