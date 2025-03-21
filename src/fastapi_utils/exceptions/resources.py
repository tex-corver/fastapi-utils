from typing import Any, Type

import core

__all__ = ["ResourceNotFoundException", "ResourceAlreadyExistsException"]


class ResourceNotFoundException(Exception):
    """"""

    def __init__(self, id: Any, resource: Type[core.BaseModel] | str):
        self.id = id
        self.resource = resource if isinstance(resource, str) else resource.__name__


class ResourceAlreadyExistsException(Exception):
    """"""

    def __init__(self, id: Any, resource: Any):
        self.id = id
        self.resource = resource
