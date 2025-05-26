import utils

import core

from . import models, schemas

__all__ = [
    "create_model",
    "handle_created_model",
]

logger = utils.get_logger()


def create_model(
    command: schemas.CreateModelCommand,
    uow: core.UnitOfWork,
):
    with uow:
        uow.repo.add(
            models.Model(
                name=command.name,
                message_id=command._id,
            )
        )
        uow.commit()


def handle_created_model(event: schemas.CreatedModelEvent):
    logger.info(event.model)
