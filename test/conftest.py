import pytest
from utils import load_schemas

@pytest.fixture(scope="session")
def schemas():
    return load_schemas()
