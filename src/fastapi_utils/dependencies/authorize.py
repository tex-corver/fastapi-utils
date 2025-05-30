import pathlib
from typing import Any

import fastapi
import jwt
import requests
import utils
from icecream import ic

from fastapi_utils import schemas

__all__ = ["tracing_headers", "get_authorization_context"]

config = utils.get_config()
encryption_config = config["application"]["encryption"]


def tracing_headers(
    session_id: str = fastapi.Header(None),
    device_id: str = fastapi.Header(None),
    authorization: str = fastapi.Header(None),
) -> schemas.TracingHeaders:
    return schemas.TracingHeaders(
        session_id=session_id,
        device_id=device_id,
        token=authorization,
    )


# TODO: Move to common lib tex-corver encryption
def get_decryption_key() -> bytes:
    path = pathlib.Path(encryption_config["jwt"]["public_key"])
    if not pathlib.Path(path).exists():
        key = download_decryption_key()
    return open(path, "rb").read()


def download_decryption_key() -> bytes:
    iam_host = config["iam"]["host"]
    url = config["iam"]["actions"]["get_public_key"]["url"]
    method = config["iam"]["actions"]["get_public_key"]["method"]
    response = requests.request(
        method=method,
        url=f"{iam_host}{url}",
    )
    # TODO: Try except block
    # TODO: Auto retry
    path = pathlib.Path(encryption_config["jwt"]["public_key"])
    key = response.content
    open(path, "wb").write(key)
    return key


def get_authorization_context(
    authorization: str = fastapi.Header(...),
) -> schemas.AuthorizationContext:
    return decrypt_authorize_token(authorization)


# TODO: Move to common lib tex-corver encryption
def decrypt_authorize_token(token: str) -> schemas.AuthorizationContext:
    key = get_decryption_key()
    payload = jwt.decode(
        token,
        key=key,
        algorithms=encryption_config["jwt"]["algorithm"],
    )
    return schemas.AuthorizationContext(**payload)
