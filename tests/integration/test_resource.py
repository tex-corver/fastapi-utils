from pprint import pprint

import pydantic as pdt
import pytest
from icecream import ic

from fastapi_utils.resources.crud import *


class Model(pdt.BaseModel):
    # id: str
    name: str


class CreateModelCommand(core.Command):
    # id: str
    name: str


class UpdateModelCommand(core.Command):
    name: str


def test_build_create_resource_code():
    SingularResponse, PluralResponse = build_response_schema(model_schema=Model)
    code = build_create_resource_code(
        resource_name="models",
        command_cls=CreateModelCommand,
        response_cls=SingularResponse,
    )
    ic(code)


def test_build_update_resource_code():
    SingularResponse, PluralResponse = build_response_schema(model_schema=Model)
    code = build_update_resource_code(
        resource_name="models",
        command_cls=UpdateModelCommand,
        response_cls=SingularResponse,
    )
    ic(code)


def test_build_router():
    SingularResponse, PluralResponse = build_response_schema(model_schema=Model)
    router = build_router(
        blueprint={
            "model_cls": Model,
            "api": {
                # "/models": {
                #     "get": ApiBlueprint(
                #         request=GetRequestBlueprint(),
                #         response=ResponseBlueprint(
                #             schema=PluralResponse,
                #         ),
                #     ),
                #     "post": ApiBlueprint(
                #         request=PostRequestBlueprint(body=CreateModelCommand),
                #         response=ResponseBlueprint(
                #             status_code=http.HTTPStatus.CREATED,
                #             schema=SingularResponse,
                #         ),
                #     ),
                # },
                "/models/{id}": {
                    "get": ApiBlueprint(
                        request=GetRequestBlueprint(),
                        response=ResponseBlueprint(
                            schema=SingularResponse,
                        ),
                    ),
                    "patch": ApiBlueprint(
                        request=PatchRequestBlueprint(body=UpdateModelCommand),
                        response=ResponseBlueprint(
                            schema=SingularResponse,
                        ),
                    ),
                    "delete": ApiBlueprint(
                        request=DeleteRequestBlueprint(),
                        response=ResponseBlueprint(
                            status_code=http.HTTPStatus.NO_CONTENT,
                        ),
                    ),
                },
            },
        },
    )
    ic(router)


@pytest.fixture
def SingularResponse():
    SingularResponse_, _ = build_response_schema(model_schema=Model)[0]
    return SingularResponse_


@pytest.fixture
def PluralResponse():
    _, PluralResponse_ = build_response_schema(model_schema=Model)[1]
    return PluralResponse_


class TestBuildCommand:
    def test_build_command(self):
        Command = build_command(action="create", model_schema=Model)
        ic(Command(**{"name": "name"}))


def bootstrap():
    uow = core.UnitOfWork()
    return core.MessageBus(uow, command_handlers={})


class TestBuildHandler:
    def test_build_handler(
        self,
        SingularResponse,
    ):
        handler = build_handler(
            resource="models",
            Command=CreateModelCommand,
            Response=SingularResponse,
        )


class TestBuildResponseModel:
    def test_build_response_model(self):
        SingularSchema, PluralSchema = build_response_schema(model_schema=Model)
        ic(SingularSchema(**{"model": Model(name="name")}))
        ic(PluralSchema(**{"models": [Model(name="name")]}))
        ic(isinstance(SingularSchema, pdt.BaseModel))
        ic(type(SingularSchema))


class TestResourceBlueprint:
    def test_build_resource_blueprint(self):
        bp = build_resource_blueprint(model_schema=Model)
        ic(bp)

    def test_build_response_blueprint(self):
        bp = build_response_blueprint(model_schema=Model)
        ic(bp)
