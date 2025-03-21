import fastapi_utils
import pydantic as pdt
import fastapi
import pytest
from fastapi import testclient
import http
import utils
from core import sqlalchemy_adapter
import sqlalchemy as sa
from typing import Callable, Any
from sqlalchemy import Table, Column, String, DateTime
from sqlalchemy.orm import registry
from core import orm
import core


class Model(core.BaseModel):
    id: str

class CreateModelCommand(pdt.BaseModel):
    id: str

@pytest.fixture
def start_orm_func() -> Callable[[], None]:
    @orm.map_once
    def _start_orm():
        config_path = utils.get_config_path()
        config = utils.load_config(config_path=config_path)
        factory = sqlalchemy_adapter.ComponentFactory(config["database"])
        metadata = sa.MetaData()
        orm_registry = factory.create_orm_registry()

        model_table = Table(
            "carts",
            metadata,
            Column("id", String(64), primary_key=True),
        )

        model_mapper = orm_registry.map_imperatively(
            class_=Model,
            local_table=model_table,
        )

        engine = factory.engine
        metadata.create_all(engine)

    return _start_orm


@pytest.fixture
def start_orm(start_orm_func: Callable[[], None]):
    start_orm_func()
    yield


@pytest.fixture
def resource_manager() -> fastapi_utils.ResourceManager:
    return fastapi_utils.ResourceManager(
        model_cls_map={
            "models": Model,
        }
    )


@pytest.fixture
def rest_client(
    resource_manager: fastapi_utils.ResourceManager,
) -> testclient.TestClient:
    app = fastapi_utils.create_app()
    fastapi_utils.set_resource_manager(resource_manager)

    def raise_not_found_exception():
        raise fastapi_utils.ResourceNotFoundException("1", Model)

    app.add_api_route(
        "/not-found-exceptions",
        raise_not_found_exception,
        methods=["GET"],
    )

    def raise_validation_error():
        CreateModelCommand()

    app.add_api_route(
        "/validation-errors",
        raise_validation_error,
        methods=["GET"],
    )

    def raise_unauthorized():
        raise fastapi.HTTPException(status_code=http.HTTPStatus.UNAUTHORIZED)

    app.add_api_route(
        "/unauthorized",
        raise_unauthorized,
        methods=["GET"],
    )

    return testclient.TestClient(app)


@pytest.mark.usefixtures("start_orm")
class TestApp:
    def test_create_app(self):
        app = fastapi_utils.create_app()
        assert app is not None
        assert isinstance(app, fastapi.FastAPI)

    @pytest.mark.parametrize(
        "path, method, status_code",
        [
            pytest.param(
                "/not-found-exceptions",
                "GET",
                http.HTTPStatus.NOT_FOUND,
                id="not-found-exception",
            ),
            pytest.param(
                "/validation-errors",
                "GET",
                http.HTTPStatus.UNPROCESSABLE_ENTITY,
                id="validation-error",
            ),
            pytest.param(
                "/unauthorized",
                "GET",
                http.HTTPStatus.UNAUTHORIZED,
                id="unauthorized",
            ),
        ],
    )
    def test_handle_exceptions(
        self,
        rest_client: testclient.TestClient,
        path: str,
        method: str,
        status_code: int,
    ):
        """"""
        response = rest_client.request(method, path)
        assert response.status_code == status_code
