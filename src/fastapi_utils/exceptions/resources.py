from typing import Any, Type

import core

__all__ = ["ResourceNotFoundException", "ResourceAlreadyExistsException"]


class ResourceNotFoundException(Exception):
    """"""

    def __init__(self, id: Any, resource: Type[core.BaseModel]):
        self.id = id
        self.resource = resource


class ResourceAlreadyExistsException(Exception):
    """"""

    def __init__(self, id: Any, resource: Any):
        self.id = id
        self.resource = resource
