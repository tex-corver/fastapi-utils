from datetime import datetime, timedelta, timezone
from typing import Any

import io_schema
import jwt
import pytest
from icecream import ic

import fastapi_utils


class TestGetAuthorizationContext:
    # TODO: indirect parametrization
    @pytest.fixture
    def payload(self):
        return {
            "user_id": "test",
            "device_id": "test",
        }

    @pytest.fixture
    def token(
        self,
        config: dict[str, Any],
        payload: dict[str, Any],
    ) -> str:
        ic(config)
        expires_delta = int(config["application"]["token"]["expiration"]["login"])
        expire = datetime.now(timezone.utc) + timedelta(minutes=expires_delta)
        payload = payload.copy() | {"exp": expire}
        SECRET_KEY = open(
            config["application"]["encryption"]["jwt"]["private_key"], "rb"
        ).read()
        encoded_jwt = jwt.encode(
            payload,
            SECRET_KEY,
            algorithm=config["application"]["encryption"]["jwt"]["algorithm"],
        )
        return encoded_jwt

    # TODO: Add more test cases with pytest.mark.parametrize
    def test_get_authorization_context(self, token: str, payload: dict[str, Any]):
        ctx = fastapi_utils.get_authorization_context(token)
        ic(ctx)
        assert isinstance(ctx, io_schema.AuthorizationContext)
        # TODO: More assertions


