import os
from icecream import ic
import pathlib
from typing import Any, Callable, Generator

import pytest
from sqlalchemy import Column, DateTime, String, Table

import core
from core import adapters, orm
from core.test.fixtures import bootstrapper
import utils

from tests.double import fake


@pytest.fixture(scope="session")
def config_path(project_path: pathlib.Path) -> pathlib.Path:
    return project_path / "tests/data/configs"


@pytest.fixture
def config(config_path: pathlib.Path) -> dict[str, Any]:
    ic(config_path)
    os.environ["CONFIG_PATH"] = str(config_path)
    return utils.load_config(config_path)


@pytest.fixture
def command_router() -> core.CommandRouter:
    return {
        fake.CreateModelCommand: fake.create_model,
    }


@pytest.fixture
def event_router() -> core.EventRouter:
    return {
        fake.CreatedModelEvent: [
            fake.handle_created_model,
        ],
    }


@pytest.fixture
def uow(config: dict[str, Any]) -> Generator[core.UnitOfWork, Any, None]:
    uow = core.UnitOfWork(config["database"])
    yield uow


@pytest.fixture
def dependencies(
    uow: core.UnitOfWork,
) -> Generator[core.Dependencies, Any, None]:
    yield {
        "uow": uow,
    }


@pytest.fixture
def start_orm_func(config: dict[str, Any]):
    @orm.map_once
    def _start_orm_func():
        component_factory = adapters.create_component_factory(config["database"])
        assert isinstance(
            component_factory, adapters.sqlalchemy_adapter.ComponentFactory
        )

        registry = component_factory.create_orm_registry()

        model_table = Table(
            "models",
            registry.metadata,
            Column("id", String(200), primary_key=True),
            Column("created_time", DateTime),
            Column("updated_time", DateTime),
            Column("message_id", String(200)),
            Column("name", String(200)),
        )

        registry.map_imperatively(fake.Model, model_table)

        engine = component_factory.engine
        registry.metadata.create_all(bind=engine)

    yield _start_orm_func


@pytest.fixture
def start_orm(start_orm_func: Callable[..., Any]):
    start_mapper = orm.map_once(start_orm_func)
    yield


@pytest.fixture
def bootstrapper_kwargs(
    start_orm_func: Any,
    command_router: core.CommandRouter,
    event_router: core.EventRouter,
    dependencies: core.Dependencies,
):
    yield {
        "use_orm": True,
        "orm_func": start_orm_func,
        "command_router": command_router,
        "event_router": event_router,
        "dependencies": dependencies,
    }


@pytest.fixture
def bus(bootstrapper: core.Bootstrapper) -> Generator[core.MessageBus, Any, None]:
    yield bootstrapper.bootstrap()
