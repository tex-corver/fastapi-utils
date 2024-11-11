import pathlib
from typing import Any

import fastapi
import io_schema
import jwt
import utils
from icecream import ic

__all__ = ["tracing_headers", "get_authorization_context"]

config = utils.get_config()
encryption_config = config["application"]["encryption"]


def tracing_headers(
    session_id: str = fastapi.Header(None),
    device_id: str = fastapi.Header(None),
    authorization: str = fastapi.Header(None),
) -> io_schema.TracingHeaders:
    return io_schema.TracingHeaders(
        session_id=session_id,
        device_id=device_id,
        token=authorization,
    )


def get_decryption_key() -> bytes:
    path = pathlib.Path(encryption_config["jwt"]["public_key"])
    if not pathlib.Path(path).exists():
        # TODO: get key from iam server
        ...
    return open(path, "rb").read()


def get_authorization_context(
    authorization: str = fastapi.Header(...),
) -> io_schema.AuthorizationContext:
    key = get_decryption_key()
    payload = jwt.decode(
        authorization,
        key=key,
        algorithms=encryption_config["jwt"]["algorithm"],
    )
    return io_schema.AuthorizationContext(**payload)
