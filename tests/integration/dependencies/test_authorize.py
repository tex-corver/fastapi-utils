# from typing import Any, Generator, List
# import uuid

# import pytest
# from icecream import ic

# import fastapi_utils
# from fastapi_utils import schemas


# def create_payload() -> dict[str, Any]:
#     return {
#         "user_id": f"user-{uuid.uuid4()}",
#         "device_id": f"device-{uuid.uuid4()}",
#     }


# @pytest.fixture
# def payloads(request) -> Generator[List[dict[str, Any]], Any, None]:
#     num_payloads = request.param
#     payloads = [create_payload() for _ in range(num_payloads)]
#     yield payloads


# class TestGetAuthorizationContext:
#     @pytest.mark.parametrize("payloads", [1], indirect=True)
#     def test_get_authorization_context(self, config, payloads: dict[str, Any]):
#         # arrange
#         payload = payloads[0]
#         token = fastapi_utils.create_access_token(
#             data=payload,
#             expires_delta=int(config["application"]["token"]["expiration"]["login"]),
#         )

#         # act
#         ctx = fastapi_utils.get_authorization_context(token)

#         # assert
#         ic(ctx)
#         assert isinstance(ctx, schemas.AuthorizationContext)
#         for key, value in payload.items():
#             assert getattr(ctx, key, None) == value
