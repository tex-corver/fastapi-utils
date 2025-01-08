import asyncio
import os
from http import HTTPStatus
from typing import Any, Dict, Iterable, Optional

from fastapi import FastAPI, HTTPException
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    REGISTRY,
    CollectorRegistry,
    Counter,
    Info,
    generate_latest,
)
import pytest
from requests import Response as TestClientResponse
from starlette.responses import Response
from starlette.testclient import TestClient

from fastapi_utils.prometheus_instrument import PrometheusInstrumentator, metrics
from icecream import ic
from prometheus_client import gc_collector, platform_collector, process_collector

setattr(TestClientResponse, "__test__", False)


class TestInstrumentation:

    @pytest.fixture
    def custom_metric(self) -> Iterable[str]:
        return ["http_request_duration_seconds"]

    @pytest.fixture
    def fastapi_app(self) -> FastAPI:
        app = FastAPI()

        collectors = list(REGISTRY._collector_to_names.keys())
        for collector in collectors:
            REGISTRY.unregister(collector)

        process_collector.ProcessCollector()
        platform_collector.PlatformCollector()
        gc_collector.GCCollector()

        @app.get("/")
        def read_root():
            return "Hello World!"

        @app.get("/sleep")
        async def sleep(seconds: float):
            await asyncio.sleep(seconds)
            return f"I have slept for {seconds}s"

        @app.get("/always_error")
        def read_always_error():
            raise HTTPException(status_code=404, detail="Not really error")

        @app.get("/always_error_httpstatus_enum")
        def read_always_error_httpstatus_enum():
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST, detail="Not really an error"
            )

        @app.get("/ignore")
        def read_ignore():
            return "Should be ignored"

        @app.get("/items/{item_id}")
        def read_item(item_id: int, q: Optional[str] = None):
            return {"item_id": item_id, "q": q}

        @app.get("/just_another_endpoint")
        def read_just_another_endpoint():
            return "Green is my pepper"

        @app.post("/items")
        def create_item(item: Dict[Any, Any]):
            return None

        return app

    @pytest.fixture
    def registry(self) -> CollectorRegistry:
        collectors = list(REGISTRY._collector_to_names.keys())
        for collector in collectors:
            REGISTRY.unregister(collector)

        process_collector.ProcessCollector()
        platform_collector.PlatformCollector()
        gc_collector.GCCollector()

        return REGISTRY

    def test_metrics_endpoint_availability(
        self, fastapi_app: FastAPI, registry: CollectorRegistry
    ):

        def http_total_requests_count():
            METRIC = Counter(
                name="http_total_requests_count",
                documentation="Total number of HTTP requests",
                labelnames=["handler", "method", "status"],
            )

            def instrumentation(info: metrics.Info) -> None:
                METRIC.labels(
                    handler=info.modified_handler,
                    method=info.method,
                    status=info.modified_status,
                ).inc()

            return instrumentation

        @fastapi_app.get("/metrics")
        def get_metrics():
            return Response(generate_latest(registry), media_type=CONTENT_TYPE_LATEST)

        instrumentor = (
            PrometheusInstrumentator(registry=registry)
            .add(http_total_requests_count())
            .instrument(fastapi_app)
        )
        client = TestClient(fastapi_app)

        client.get("/")
        client.get("/")

        response = client.get("/metrics")

        assert response.status_code == 200
        assert b"http_total_requests_count" in response.content
        assert (
            b"# HELP http_total_requests_count_total Total number of HTTP requests"
            in response.content
        )
        assert (
            b'http_total_requests_count_total{handler="/",method="GET",status="200"} 2.0'
            in response.content
        )

    # ------------------------------------------------------------------------------
    # Test gzip

    def test_default_metric_name(
        self, fastapi_app: FastAPI, registry: CollectorRegistry
    ):
        @fastapi_app.get("/metrics")
        def get_metrics():
            return Response(generate_latest(registry), media_type=CONTENT_TYPE_LATEST)

        instrumentor = PrometheusInstrumentator(registry=registry).instrument(
            fastapi_app
        )
        client = TestClient(fastapi_app)

        client.get("/")

        response = client.get("/metrics")

        assert response.status_code == 200
        assert b"http_requests_total" in response.content
        assert b"http_request_size_bytes" in response.content
        assert b"http_response_size_bytes" in response.content
        assert b"http_request_duration_highr_seconds" in response.content
        assert b"http_request_duration_seconds" in response.content

    def test_grouped_status_codes_with_enumeration(
        self, fastapi_app: FastAPI, registry: CollectorRegistry
    ):
        @fastapi_app.get("/metrics")
        def get_metrics():
            return Response(generate_latest(registry), media_type=CONTENT_TYPE_LATEST)

        instrumentor = PrometheusInstrumentator(registry=registry).instrument(
            fastapi_app
        )
        client = TestClient(fastapi_app)

        client.get("/always_error_httpstatus_enum")
        response = client.get("/metrics")

        assert b'status="400"' in response.content
        assert b'handler="/always_error_httpstatus_enum"' in response.content

    def test_untemplated_path(self, fastapi_app: FastAPI, registry: CollectorRegistry):
        @fastapi_app.get("/metrics")
        def get_metrics():
            return Response(generate_latest(registry), media_type=CONTENT_TYPE_LATEST)

        instrumentor = PrometheusInstrumentator(registry=registry).instrument(
            fastapi_app
        )
        client = TestClient(fastapi_app)

        client.get("/")
        client.get("/")
        client.get("/404_does_not_exist")

        response = client.get("/metrics")

        assert b'handler="/404_does_not_exist"' not in response.content
        assert b'handler="none"' in response.content
