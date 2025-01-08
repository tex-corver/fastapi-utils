import asyncio
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
import pytest
from starlette.testclient import TestClient

from fastapi_utils.prometheus_instrument import PrometheusInstrumentator
from icecream import ic

from prometheus_client import REGISTRY, CollectorRegistry
from prometheus_client import gc_collector, platform_collector, process_collector


class TestPrometheusInstrumentatorExpose:

    @pytest.fixture
    def fastapi_app(self) -> FastAPI:
        app = FastAPI()

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

    def test_expose_default_content_type(self, fastapi_app, registry):
        insrumentor = (
            PrometheusInstrumentator(registry=registry)
            .instrument(fastapi_app)
            .expose(fastapi_app)
        )
        client = TestClient(fastapi_app)

        response = client.get("/metrics")
        ic(response.headers.items())
        assert (
            "text/plain; version=0.0.4; charset=utf-8; charset=utf-8"
            not in response.headers.values()
        )

    def test_fastapi_app_expose(self, fastapi_app, registry):
        insrumentor = (
            PrometheusInstrumentator(registry=registry)
            .instrument(fastapi_app)
            .expose(fastapi_app)
        )
        client = TestClient(fastapi_app)

        response = client.get("/metrics")

        assert response.status_code == 200
