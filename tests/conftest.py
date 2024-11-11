import pathlib

import pytest


@pytest.fixture(scope="session")
def project_path() -> pathlib.Path:
    return pathlib.Path(__file__).parents[1]
