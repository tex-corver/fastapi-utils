# from typing import Generator, Any
# import uuid

# import pytest

# import fastapi_utils
# import core
# from core import views

# from tests.double import fake


# @pytest.fixture
# def resource_manager():
#     yield fastapi_utils.ResourceManager(
#         model_cls_map={
#             "models": fake.Model,
#         }
#     )


# class TestResourceManager:
#     @pytest.fixture
#     def model(
#         self,
#         bus: core.MessageBus,
#     ) -> Generator[fake.Model, Any, None]:
#         command = fake.CreateModelCommand(name="test")
#         bus.handle(command)
#         view = views.get_view()
#         with view.fetch_model(fake.Model, message_id=command._id) as model:
#             yield model

#     def test_get_model_cls(
#         self,
#         resource_manager,
#     ):
#         model_cls = resource_manager.get_model_cls("models")
#         assert model_cls == fake.Model

#     def test_verify_resource_inexisted(
#         self,
#         resource_manager,
#         model,
#     ):
#         id = str(uuid.uuid4())
#         resource_manager.verify_resource_inexisted("models", id=id)

#     def test_verify_resource_inexisted_with_error(
#         self,
#         resource_manager,
#         model,
#     ):
#         with pytest.raises(
#             ValueError,
#             match=f"{fake.Model.__name__} already existed: {{'id': '{model.id}'}}",
#         ):
#             resource_manager.verify_resource_inexisted("models", id=model.id)

#     def test_verify_resource_existed(
#         self,
#         resource_manager,
#         model,
#     ):
#         resource_manager.verify_resource_existed("models", id=model.id)

#     def test_verify_resource_existed_with_error(
#         self,
#         resource_manager,
#         model,
#     ):
#         id = str(uuid.uuid4())
#         with pytest.raises(
#             ValueError,
#             match=f"{fake.Model.__name__} not found: {{'id': '{id}'}}",
#         ):
#             resource_manager.verify_resource_existed("models", id=id)
