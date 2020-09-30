import pytest
from utils import ExitCode


@pytest.mark.skipif()
def test_list_local_directories(run):
    result = run(['ls', 'foobar'])
    assert result == ExitCode(0)
