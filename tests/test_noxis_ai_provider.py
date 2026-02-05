import pytest
from noxis.ai import provider
import json

@pytest.fixture
def api_client():
    return provider.APIProvider()

# Add your tests here instead of the existing ones
