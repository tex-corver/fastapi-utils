import fastapi
import pydantic as pdt
from fastapi_utils.middlewares.exception_handlers import *
from fastapi_utils.exceptions.resources import *


def create_app() -> fastapi.FastAPI:
    app = fastapi.FastAPI()
    app.add_exception_handler(
        ResourceNotFoundException,
        handle_resource_not_found,
    )
    app.add_exception_handler(
        ResourceAlreadyExistsException,
        handle_resource_already_exists,
    )
    app.add_exception_handler(
        pdt.ValidationError,
        handle_validation_error,
    )
    return app
