from utils import call, create_client, ExitCode
# This is not ideal, but it is fine for demo purposes
from hooks import *
import logging
import time

import docker
import pytest


def get_logger(name):
    return logging.getLogger('conftest.%s' % name)


@pytest.fixture(scope='session')
def client():
    return create_client()


@pytest.fixture(scope='session', autouse=True)
def local_container(client, request):
    image = 'localbuild:flask'
    container = start_container(
        client,
        image=image,
        name='flask_functional',
        environment={},
        detach=True,
        ports={'5000/tcp': 5000}
    )

    no_keep_alive = request.config.getoption("--nokeepalive", False)
    if no_keep_alive:
        # Do not leave the container running and tear it down at the end of the session
        request.addfinalizer(lambda: teardown_container(client, container=container))

    return container


def teardown_container(client, container=None, name=None):
    logger = get_logger('teardown_container')
    container_name = name or container.name
    if name:
        container_name = name
    else:
        container_name = container.name
    logger.debug('Tearing down container: %s', container_name)
    containers = client.containers.list(all=True, filters={'name': container_name})
    # TODO: check if stop/remove can take a force=True param
    for available_container in containers:
        available_container.stop()
        available_container.remove()


def start_container(client, image, name, environment, ports, detach=True):
    """
    Start a container, wait for (successful) completion of entrypoint
    and raise an exception with container logs otherwise
    """
    logger = get_logger('start_container')
    logger.info('will try to start container image %s', image)
    try:
        container = client.containers.get(name)
        if container.status != 'running':
            logger.info('%s container found but not running, will start it', name)
            container.start()
    except docker.errors.NotFound:
        logger.info('%s container not found, will start it', name)
        container = client.containers.run(
            image=image,
            name=name,
            environment={},
            detach=True,
            ports=ports,
        )

    start = time.time()
    while time.time() - start < 70:
        out, err, code = call(
            ['curl', 'localhost:5000'],
        )
        if code == ExitCode(0):
            # This path needs to be hit when the container is ready to be
            # used, if this is not reached, then an error needs to bubble
            # up
            return container
        time.sleep(2)

    logger.error('Aborting tests: unable to verify a healthy status from container')
    # If 70 seconds passed and curl wasn't able to determine an OK
    # status from the webapp then failure needs to be raised with as much
    # logging as possible. Can't assume the container is healthy even if the
    # exit code is 0
    print("[ERROR][setup] failed to setup container")
    for line in out.split('\n'):
        print("[ERROR][setup][stdout] {}".format(line))
    for line in err.split('\n'):
        print("[ERROR][setup][stderr] {}".format(line))
    raise RuntimeError()


def remove_container(client, container_name):
    # remove any existing test container
    for test_container in client.containers.list(all=True):
        if test_container.name == container_name:
            test_container.stop()
            test_container.remove()


@pytest.fixture
def run():

    def _run(command):
        out, err, code = call(command)
        # code will have out and err on it already
        return code
    return _run
