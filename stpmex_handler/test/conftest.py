from stpmex_handler import views
import pytest


@pytest.fixture
def app():
    client = views.app.test_client()
    client.debug = True
    return client
