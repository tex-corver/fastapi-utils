import fastapi
import http
from typing import NewType, TypeVar, Generic, Type
import core
import utils

__all__ = [
    "verify_resource_inexisted",
    "verify_resource_existed",
    "get_resource_manager",
    "set_resource_manager",
    "ResourceManager",
]

T = TypeVar("T", bound=core.BaseModel)
ModelClsMapper = NewType("ModelClsMapper", dict[str, Type[core.BaseModel]])


class ResourceManager:
    def __init__(self, model_cls_map: ModelClsMapper):
        self.model_cls_map = model_cls_map
        self.views = core.View()

    def get_model_cls(self, resource_type: str) -> Type[T]:
        return self.model_cls_map[resource_type]

    def verify_resource_inexisted(self, resource_type: str, **identifiers) -> None:
        model_cls = self.get_model_cls(resource_type)
        with self.views.fetch_model(model_cls, **identifiers) as model:
            if model is None:
                raise ValueError(f"{model_cls.__name__} already existed: {identifiers}")

    def verify_resource_existed(self, resource_type: str, **identifiers) -> None:
        model_cls = self.get_model_cls(resource_type)
        with self.views.fetch_model(model_cls, **identifiers) as model:
            if model is None:
                raise ValueError(f"{model_cls.__name__} not found: {identifiers}")


RESOURCE_MANAGER = None


def get_resource_manager() -> ResourceManager:
    global RESOURCE_MANAGER
    return RESOURCE_MANAGER


def set_resource_manager(resource_manager: ResourceManager):
    global RESOURCE_MANAGER
    RESOURCE_MANAGER = resource_manager


async def verify_resource_inexisted(request: fastapi.Request):
    root_path = request.scope["root_path"]
    full_path = request.scope["path"]
    path = request.url.path

    path_parts = path.split("/")
    if len(path_parts) < 1:
        return

    resource_type = path_parts[1]
    resource_manager = get_resource_manager()
    try:
        resource_manager.verify_resource_inexisted(
            resource_type=resource_type,
            **identifiers,
        )
    except ValueError as e:
        raise fastapi.HTTPException(
            status_code=http.HTTPStatus.CONFLICT,
            detail=str(e),
        )


async def verify_resource_existed(
    request: fastapi.Request,
    id: int | str,
):
    if id is None:
        return
    root_path = request.scope["root_path"]
    full_path = request.scope["path"]
    path = request.url.path

    path_parts = path.split("/")
    if len(path_parts) < 1:
        return

    resource_type = path_parts[1]
    resource_manager = get_resource_manager()
    try:
        resource_manager.verify_resource_existed(
            resource_type=resource_type,
            id=id,
        )
    except ValueError as e:
        raise fastapi.HTTPException(
            status_code=http.HTTPStatus.NOT_FOUND,
            detail=str(e),
        )