import http
import re
import types
from typing import Any, Type

import core
import fastapi
import inflect
import pydantic as pdt
from pydantic._internal._model_construction import ModelMetaclass

inflect_engine = inflect.engine()

STATUS_CODE = {
    "get": http.HTTPStatus.OK,
    "post": http.HTTPStatus.CREATED,
    "patch": http.HTTPStatus.OK,
    "delete": http.HTTPStatus.NO_CONTENT,
    "query": http.HTTPStatus.OK,
}


class RequestBlueprint(pdt.BaseModel):
    params: dict[str, Any] | None = None
    body: core.Command | None = None
    data: dict[str, Any] | None = None


class GetRequestBlueprint(RequestBlueprint):
    body: None = None


class PostRequestBlueprint(RequestBlueprint):
    body: Type[core.Command]


class PatchRequestBlueprint(PostRequestBlueprint):
    """"""


class DeleteRequestBlueprint(RequestBlueprint):
    body: None = None


class ResponseBlueprint(pdt.BaseModel):
    model_config = pdt.ConfigDict(arbitrary_types_allowed=True)
    status_code: int = http.HTTPStatus.OK
    schema: Type[pdt.BaseModel] | Type[ModelMetaclass] | None = None


class ApiBlueprint(pdt.BaseModel):
    """"""

    request: RequestBlueprint
    response: ResponseBlueprint


camel_pattern = re.compile(r"(?<!^)(?=[A-Z])")


class ResourceBlueprint(pdt.BaseModel):
    get: ApiBlueprint
    post: ApiBlueprint
    patch: ApiBlueprint
    delete: ApiBlueprint
    query: ApiBlueprint


def camel_to_snake(name: str):
    return camel_pattern.sub("_", name).lower()


def build_response_schema(
    model_schema: pdt.BaseModel,
):
    base_schema_name = model_schema.__name__
    plural_schema_name = inflect_engine.plural(base_schema_name)
    return (
        pdt.create_model(
            f"{base_schema_name}Response",
            **{camel_to_snake(base_schema_name): (model_schema, ...)},
        ),
        pdt.create_model(
            f"{plural_schema_name}Response",
            **{camel_to_snake(plural_schema_name): (list[model_schema], ...)},
        ),
    )


def build_response_blueprint(
    model_schema: pdt.BaseModel,
):
    SingularSchema, PluralSchema = build_response_schema(model_schema)
    response = ResponseBlueprint(
        schema=SingularSchema,
    )
    return response


ACTION = {
    "post": "create",
    "patch": "update",
}


def extract_schema_fields(schema: pdt.BaseModel) -> dict[str, tuple[Any, Any, Any]]:
    fields_dict = {}
    for field_name, field_info in schema.model_fields.items():
        fields_dict[field_name] = (
            field_info.annotation[0].__name__,
            # field_info.default_factory,
            # field_info.default,
        )
    return fields_dict


def build_command(
    action: str,
    model_schema: pdt.BaseModel,
):
    """"""
    Command = pdt.create_model(
        f"{action.capitalize()}{model_schema.__name__}Command",
        **extract_schema_fields(model_schema),
    )
    return Command


def snake_to_camel(snake_str: str) -> str:
    components = snake_str.split("_")
    return "".join(x.title() for x in components)


def build_resource_blueprint(
    model_schema: pdt.BaseModel,
    blueprint: dict[str, Any] = None,
):
    SingularSchema, PluralSchema = build_response_schema(model_schema)
    bp = ResourceBlueprint(
        get=ApiBlueprint(
            request=GetRequestBlueprint(),
            response=ResponseBlueprint(schema=SingularSchema),
        ),
        post=ApiBlueprint(
            request=PostRequestBlueprint(body=core.Command()),
            response=ResponseBlueprint(
                status_code=http.HTTPStatus.CREATED,
                schema=SingularSchema,
            ),
        ),
        patch=ApiBlueprint(
            request=PatchRequestBlueprint(body=core.Command()),
            response=ResponseBlueprint(schema=SingularSchema),
        ),
        delete=ApiBlueprint(
            request=DeleteRequestBlueprint(),
            response=ResponseBlueprint(status_code=http.HTTPStatus.NO_CONTENT),
        ),
        query=ApiBlueprint(
            request=RequestBlueprint(params={}),
            response=ResponseBlueprint(schema=PluralSchema),
        ),
    )
    return bp


def build_create_resource_code(
    resource_name: str,
    command_cls: Type[core.Command],
    response_cls: Type[pdt.BaseModel],
    model_cls: Type[object],
) -> str:
    resource_name_singular = inflect_engine.singular_noun(resource_name)
    if resource_name_singular is False:
        resource_name_singular = resource_name
    model_cls = snake_to_camel(resource_name_singular)
    code = f"""
def create_{resource_name_singular}(
    command: {command_cls.__name__}
) -> {response_cls.__name__}:
    bus = bootstrap()
    bus.handle(command)
    resource: models.{model_cls} = view.fetch_model(
        model_cls=models.{model_cls},
        creation_id=command._id,
    )
    return {response_cls.__name__}({resource_name_singular}=resource)
    """
    return code


def build_update_resource_code(
    resource_name: str,
    command_cls: Type[core.Command],
    response_cls: Type[pdt.BaseModel],
    model_cls: Type[object],
) -> str:
    resource_name_singular = inflect_engine.singular_noun(resource_name)
    if resource_name_singular is False:
        resource_name_singular = resource_name
    model_cls = snake_to_camel(resource_name_singular)
    code = f"""
def update_{resource_name_singular}(
    command: {command_cls.__name__},
    id: str | int,
) -> {response_cls.__name__}:
    bus = bootstrap()
    command.resource_id = id
    bus.handle(command)
    resource: {model_cls} = view.fetch_model(
        model_cls=models.{model_cls},
        creation_id=command._id,
    )
    return {response_cls.__name__}({resource_name_singular}=resource)
    """
    return code


def build_get_resource_code(
    resource_name: str,
    response_cls: Type[pdt.BaseModel],
    model_cls: Type[object],
) -> str:
    resource_name_singular = inflect_engine.singular_noun(resource_name)
    if resource_name_singular is False:
        resource_name_singular = resource_name
    response_cls_name = f"{response_cls.__module__}.{response_cls.__name__}"
    model_cls_name = f"{model_cls.__module__}.{model_cls.__name__}"
    code = f"""
from {model_cls.__module__} import {model_cls.__name__}

def get_{resource_name_singular}(id: str | int) -> {response_cls_name}:
    resource: {model_cls_name} = view.fetch_model(
        model_cls={model_cls_name},
        creation_id=id,
    )
    return {response_cls_name}({resource_name_singular}=resource)
    """
    return code


def build_delete_resource_code(
    resource_name: str,
    command_cls: Type[core.Command],
) -> str:
    resource_name_singular = inflect_engine.singular_noun(resource_name)
    if resource_name_singular is False:
        resource_name_singular = resource_name
    model_cls = snake_to_camel(resource_name_singular)
    code = f"""
def delete_{resource_name_singular}(id: str | int) -> None:
    command = {command_cls.__name__}(_id=id)
    bus = bootstrap()
    bus.handle(command)
    """
    return compile(code, "<string>", "exec")


def build_handler(
    method: str,
    resource: str,
    response_cls: Type[pdt.BaseModel],
    model_cls: Type[object],
    command_cls: Type[core.Command] | None = None,
):
    match method:
        case "get":
            code = build_get_resource_code(
                resource,
                response_cls,
                model_cls=model_cls,
            )
        case "post":
            # code = build_create_resource_code(
            #     resource,
            #     command_cls,
            #     response_cls,
            # )
            code = ""
        case "patch":
            # code = build_update_resource_code(
            #     resource,
            #     command_cls,
            #     response_cls,
            # )
            code = ""
        case "delete":
            # code = build_delete_resource_code(
            #     resource,
            #     command_cls,
            # )
            code = ""
    local_ns = {}
    exec(
        code,
        globals(),
        local_ns,
    )
    return local_ns[f"create_{resource}"]


def build_router(
    blueprint: dict[str, dict[str, ApiBlueprint]],
) -> fastapi.APIRouter:
    """"""
    router = fastapi.APIRouter()
    resource = list(blueprint["api"].keys())[0].split("/")[1]
    for api in blueprint["api"]:
        for method in blueprint["api"][api]:
            bp = blueprint["api"][api][method]
            f = build_handler(
                method=method,
                resource=resource,
                response_cls=bp.response.schema,
                command_cls=bp.request.body,
                model_cls=blueprint["model_cls"],
            )
            router.add_api_route(
                path=f"/{api}",
                endpoint=f,
                methods=[method.upper()],
            )
            print(bp)
            print(bp.request)
            print(bp.response)


class CRUDResource:
    def __init__(
        self,
        name: str,
        # model_schema: pdt.BaseModel,
        blueprint: dict[str, dict[str, ApiBlueprint]],
        **kwargs,
    ):
        """"""
        self.name = name
        self.blueprint = blueprint

    def _build_response_schema(self):
        self.schemas

    def _build_api_blueprint(
        self,
        **kwargs,
    ):
        return ApiBlueprint(
            request=RequestBlueprint(),
            response=ResponseBlueprint(),
        )
