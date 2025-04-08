# TODO: Refacto
# import core
# from fastapi import FastAPI
# import io_schema
# import utils
# from starlette.middleware.base import BaseHTTPMiddleware
# import message_broker
# import time
# from fastapi.requests import Request

# config = utils.get_config()


# class CalledApiEvent(core.Event):
#     entry: io_schema.Entry


# class TrackingRequestMiddleware(BaseHTTPMiddleware):
#     def __init__(self, app: FastAPI, *, publisher: message_broker.Publisher = None):
#         if publisher is None:
#             publisher = message_broker.Publisher(config["message_broker"])
#         self.publisher = publisher
#         super().__init__(app)

#     def publish_entry(self, entry: io_schema.Entry):
#         event = CalledApiEvent(entry=entry)
#         self.publisher.publish(event)

#     async def dispatch(self, request: Request, call_next):
#         response = await call_next(request)
#         start_time = time.time()
#         # TODO: get dataset_before and dataset_after
#         # TODO: get user
#         entry = io_schema.Entry(
#             url=str(request.url),
#             method=request.method,
#             timestamp=int(start_time),
#             user="anonymous",
#             dataset_before=None,
#             dataset_after=None,
#             status=str(response.status_code),
#         )
#         self.publish_entry(entry)
#         return response
