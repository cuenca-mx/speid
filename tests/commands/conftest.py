import pytest

from speid import app


@pytest.fixture
def runner():
    app.testing = True
    runner = app.test_cli_runner()
    return runner
