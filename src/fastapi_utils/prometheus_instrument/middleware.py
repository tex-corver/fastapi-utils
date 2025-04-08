from __future__ import annotations

from http import HTTPStatus
from timeit import default_timer
from typing import Callable, Sequence, Tuple

from prometheus_client import REGISTRY, CollectorRegistry, Gauge
from fastapi.applications import FastAPI
from fastapi.datastructures import Headers
from fastapi.requests import Request
from fastapi.responses import Response
from starlette.types import Message, Receive, Scope, Send

from . import metrics, routing


class PrometheusMiddleware:
    def __init__(
        self,
        app: FastAPI,
        *,
        instrumentations: Sequence[Callable[[metrics.Info], None]] = (),
        metric_namespace: str = "",
        metric_subsystem: str = "",
        registry: CollectorRegistry = REGISTRY,
    ):
        self.app = app
        self.registry = registry

        if instrumentations:
            self.instrumentations = instrumentations
        else:
            default_instrumentation = metrics.default(
                metric_namespace=metric_namespace,
                metric_subsystem=metric_subsystem,
                registry=self.registry,
            )
            if default_instrumentation:
                self.instrumentations = [default_instrumentation]
            else:
                self.instrumentations = []

        self.inprogress = Gauge(
            name="http_requests_inprogress",
            documentation="Number of HTTP requests in progress.",
            labelnames=("method", "handler"),
            multiprocess_mode="livesum",
        )

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        request = Request(scope)
        start_time = default_timer()

        handler, is_templated = self._get_handler(request)
        handler = handler if is_templated else "none"

        inprogress = self.inprogress.labels(request.method, handler)
        inprogress.inc()

        status_code = 500
        headers = []
        body = b""
        response_start_time = None

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                nonlocal status_code, headers, response_start_time
                headers = message["headers"]
                status_code = message["status"]
                response_start_time = default_timer()
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as exc:
            raise exc
        finally:
            status = (
                str(status_code.value)
                if isinstance(status_code, HTTPStatus)
                else str(status_code)
            )

            duration = max(default_timer() - start_time, 0.0)
            duration = round(duration, 4)

            inprogress.dec()

            response = Response(
                content=body,
                headers=Headers(raw=headers),
                status_code=status_code,
            )

            info = metrics.Info(
                request=request,
                response=response,
                method=request.method,
                modified_handler=handler,
                modified_status=status,
                modified_duration=duration,
            )

            for instrumentation in self.instrumentations:
                instrumentation(info)

    def _get_handler(self, request: Request) -> Tuple[str, bool]:
        """Extracts either template or (if no template) path.

        Args:
            request (Request): Python Requests request object.

        Returns:
            Tuple[str, bool]: Tuple with two elements. First element is either
                template or if no template the path. Second element tells you
                if the path is templated or not.
        """
        route_name = routing.get_route_name(request)
        return route_name or request.url.path, True if route_name else False
