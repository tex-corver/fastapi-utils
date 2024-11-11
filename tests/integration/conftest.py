import os
from icecream import ic
import pathlib
from typing import Any

import pytest
import utils


@pytest.fixture(scope="session")
def config_path(project_path: pathlib.Path) -> pathlib.Path:
    return project_path / "tests/data/configs"


@pytest.fixture
def config(config_path: pathlib.Path) -> dict[str, Any]:
    ic(config_path)
    os.environ["CONFIG_PATH"] = str(config_path)
    return utils.load_config(config_path)
