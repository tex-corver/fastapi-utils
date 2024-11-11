from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
import utils


def create_access_token(
    data: dict[str, Any],
    expires_delta: int = None,
) -> str:
    config = utils.get_config()
    encryption_config = config["application"]["encryption"]
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_delta)
    payload = data.copy() | {"exp": expire}
    SECRET_KEY = open(encryption_config["jwt"]["private_key"], "rb").read()
    encoded_jwt = jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=encryption_config["jwt"]["algorithm"],
    )
    return encoded_jwt
