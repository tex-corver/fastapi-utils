__all__ = [
    "Model",
]

import core
from tests.double.fake import schemas


class Model(core.BaseModel):
    name: str

    def __init__(
        self,
        name: str,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.name = name
        self.events.append(schemas.CreatedModelEvent(model=self))

    def __eq__(self, other):
        return self.name == other.name
