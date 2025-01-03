from enum import Enum
from typing import Any, Callable, List, Optional, cast

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    REGISTRY,
    CollectorRegistry,
    generate_latest,
)
from fastapi.applications import FastAPI
from fastapi.requests import Request
from fastapi.responses import Response

from .middleware import PrometheusMiddleware
from . import metrics


class PrometheusInstrumentator:
    def __init__(
        self,
        registry: Optional[CollectorRegistry] = None,
    ):
        """Create a Prometheus FastAPI Instrumentator.
        Args:
            registry (CollectorRegistry): A custom Prometheus registry to use. If not
                provided, the default `REGISTRY` will be used. This can be useful if
                you need to run multiple apps at the same time, with their own
                registries, for example during testing.
        """
        self.instrumentations: list[Callable[[metrics.Info], None]] = []

        self.registry = REGISTRY
        if registry:
            self.registry = registry

    def instrument(
        self,
        app: FastAPI,
        metric_namespace: str = "",
        metric_subsystem: str = "",
    ) -> "PrometheusInstrumentator":
        """Performs the instrumentation by adding middleware.

        The middleware iterates through all `instrumentations` and executes them.

        Args:
            app: FastAPI app instance.

        Raises:
            e: Only raised if app itself throws an exception.

        Returns:
            self: PrometheusInstrumentator. Builder Pattern.

        """

        app.add_middleware(
            PrometheusMiddleware,
            metric_namespace=metric_namespace,
            metric_subsystem=metric_subsystem,
            instrumentations=self.instrumentations,
            registry=self.registry,
        )

        return self

    def expose(
        self,
        app: FastAPI,
        *,
        endpoint: str = "/metrics",
        tags: Optional[List[str | Enum]] = None,
        **kwargs: Any,
    ) -> "PrometheusInstrumentator":
        """Exposes endpoint for metrics.

        Args:
            app: App instance. Endpoint will be added to this app. This can be
            a FastAPI app.

            endpoint: Endpoint on which metrics should be exposed.

            include_in_schema: Should the endpoint show up in the documentation?

            tags (List[str], optional): If you manage your routes with tags.
                Defaults to None. Will passed to FastAPI app.

            kwargs: Will passed to FastAPI app.

        Returns:
            self: PrometheusInstrumentator. Builder Pattern.
        """

        def metrics(request: Request) -> Response:
            """Endpoint that serves Prometheus metrics."""

            resp = Response(content=generate_latest(self.registry))
            resp.headers["Content-Type"] = CONTENT_TYPE_LATEST

            return resp

        app.get(endpoint, include_in_schema=True, tags=tags, **kwargs)(metrics)

        return self

    def add(
        self,
        *instrumentation_function: Optional[Callable[[metrics.Info], None]],
    ) -> "PrometheusInstrumentator":
        """Adds function to list of instrumentations.

        Args:
            instrumentation_function: Function
                that will be executed during every request handler call (if
                not excluded). See above for detailed information on the
                interface of the function.

        Returns:
            self: PrometheusInstrumentator. Builder Pattern.
        """

        for func in instrumentation_function:
            self.instrumentations.append(cast(Callable[[metrics.Info], None], func))

        return self
