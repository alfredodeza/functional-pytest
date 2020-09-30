import os
import logging
import pytest
import subprocess
import docker
from docker.errors import DockerException


def create_client():
    logger = logging.getLogger('conftest.create_client')
    try:
        c = docker.DockerClient(base_url='unix://var/run/docker.sock', version="auto")
        api_client = docker.APIClient(base_url='unix://var/run/docker.sock')
        # XXX ?
        c.run = run(api_client)
        return c
    except DockerException as e:
        logger.exception('Unable to connect to a docker socket')
        raise pytest.UsageError("Could not connect to a running docker socket: %s" % str(e))


def run(client):
    def run_command(container_id, command):
        created_command = client.exec_create(container_id, cmd=command)
        result = client.exec_start(created_command)
        exit_code = client.exec_inspect(created_command)['ExitCode']
        if exit_code != 0:
            msg = 'Non-zero exit code (%d) for command: %s' % (exit_code, command)
            raise(AssertionError(result), msg)
        return result
    return run_command


class ExitCode(int):
    """
    For rich comparison in Pytest, the objects being compared can be
    introspected to provide more context to a failure. The idea here is that
    when the exit code is not expected, a custom Pytest hook can provide the
    `stderr` and `stdout` aside from just the exit code. The normal `int`
    behavior is preserved.
    """
    def __init__(self, code):
        self.code = code
        self.stderr = ''
        self.stdout = ''


def call(command, **kw):
    """
    Similar to ``subprocess.Popen`` with the following changes:

    * returns stdout, stderr, and exit code (vs. just the exit code)
    * logs the full contents of stderr and stdout (separately) to the file log

    By default, no terminal output is given, not even the command that is going
    to run.

    Useful when system calls are needed to act on output, and that same output
    shouldn't get displayed on the terminal.

    :param terminal_verbose: Log command output to terminal, defaults to False, and
                             it is forcefully set to True if a return code is non-zero
    :param split: Instead of returning output as a long string, split on newlines, and then also
                  split on whitespace. Useful when output keeps changing when tabbing on custom
                  lengths
    """
    logger = logging.getLogger('conftest.call')
    stdout = logging.getLogger('conftest.call.stdout')
    stderr = logging.getLogger('conftest.call.stderr')
    log_verbose = kw.pop('log_verbose', False)
    command_msg = "Running command: %s" % ' '.join(command)
    logger.info(command_msg)
    env = kw.pop('env', None)
    split = kw.pop('split', False)
    existing_env = os.environ.copy()
    if env:
        for key, value in env.items():
            existing_env[key] = value

    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.PIPE,
        close_fds=True,
        env=existing_env,
        **kw
    )
    stdout_stream = process.stdout.read()
    stderr_stream = process.stderr.read()
    returncode = process.wait()
    if not isinstance(stdout_stream, str):
        stdout_stream = stdout_stream.decode('utf-8')
    if not isinstance(stderr_stream, str):
        stderr_stream = stderr_stream.decode('utf-8')

    if returncode != 0:
        # set to true so that we can log the stderr/stdout that callers would
        # do anyway
        log_verbose = True

    # the following can get a messed up order in the log if the system call
    # returns output with both stderr and stdout intermingled. This separates
    # that.
    if log_verbose:
        for line in stdout_stream.splitlines():
            stdout.info(line)
        for line in stderr_stream.splitlines():
            stderr.info(line)

    returncode = ExitCode(returncode)
    returncode.stderr = stderr_stream
    returncode.stdout = stdout_stream

    if split:
        stdout_stream = [line.split() for line in stdout_stream.split('\n')]
        stderr_stream = [line.split() for line in stderr_stream.split('\n')]

    return stdout_stream, stderr_stream, returncode
