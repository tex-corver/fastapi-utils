import fastapi
import traceback
import pydantic as pdt
import http
from fastapi import responses
import utils
from fastapi_utils.exceptions import *


logger = utils.get_logger()


async def handle_resource_not_found(
    request: fastapi.Request,
    exc: ResourceNotFoundException,
):
    logger.error(traceback.format_exc())
    return responses.JSONResponse(
        status_code=http.HTTPStatus.NOT_FOUND,
        content={
            "message": str(exc),
            "traceback": traceback.format_exc(),
        },
    )


async def handle_resource_already_exists(
    request: fastapi.Request,
    exc: ResourceAlreadyExistsException,
):
    logger.error(traceback.format_exc())
    return responses.JSONResponse(
        status_code=http.HTTPStatus.CONFLICT,
        content={
            "message": str(exc),
            "traceback": traceback.format_exc(),
        },
    )


async def handle_validation_error(
    request: fastapi.Request,
    exc: pdt.ValidationError,
):
    logger.error(traceback.format_exc())
    return responses.JSONResponse(
        status_code=http.HTTPStatus.UNPROCESSABLE_ENTITY,
        content={
            "message": str(exc),
            "traceback": traceback.format_exc(),
        },
    )




async def handle_unauthorized(
    request: fastapi.Request,
    exc: fastapi.HTTPException,
):
    logger.error(traceback.format_exc())
    return responses.JSONResponse(
        status_code=http.HTTPStatus.UNAUTHORIZED,
        content={
            "message": str(exc),
            "traceback": traceback.format_exc(),
        },
    )


async def handle_pydantic_error(
    request: fastapi.Request,
    exc: pdt.ValidationError,
):
    logger.error(traceback.format_exc())
    return responses.JSONResponse(
        status_code=http.HTTPStatus.BAD_REQUEST,
        content={
            "message": str(exc),
            "traceback": traceback.format_exc(),
        },
    )
