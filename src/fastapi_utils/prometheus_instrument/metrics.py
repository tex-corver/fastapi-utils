"""
This module contains ready-to-use functions that can be passed on to the
instrumentator instance with the `add()` method. The idea behind this is to
make the types of metrics you want to export with the instrumentation easily
customizable. The default instrumentation function `default` can also be found
here. And of-course, I find and copy from internet.

If your requirements are really specific or very extensive it makes sense to
create your own instrumentation function instead of combining several functions
from this module.
"""

from typing import Callable, Optional, Sequence

from prometheus_client import (
    REGISTRY,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    Summary,
)
from fastapi.requests import Request
from fastapi.responses import Response


class Info:
    def __init__(
        self,
        request: Request,
        response: Optional[Response],
        method: str,
        modified_handler: str,
        modified_status: str,
        modified_duration: float,
    ):
        """Creates Info object that is used for instrumentation functions.

        This is the only argument that is passed to the instrumentation functions.

        Args:
            request (Request): Python Requests request object.
            response (Response or None): Python Requests response object.
            method (str): Unmodified method of the request.
            modified_handler (str): Handler representation after processing by
                instrumentator. For example grouped to `none` if not templated.
            modified_status (str): Status code representation after processing
                by instrumentator. For example grouping into `2xx`, `3xx` and so on.
            modified_duration (float): Latency representation after processing
                by instrumentator. For example rounding of decimals. Seconds.

        """

        self.request = request
        self.response = response
        self.method = method
        self.modified_handler = modified_handler
        self.modified_status = modified_status
        self.modified_duration = modified_duration


def _is_duplicated_time_series(error: ValueError) -> bool:
    return any(
        map(
            error.args[0].__contains__,
            [
                "Duplicated timeseries in CollectorRegistry:",
                "Duplicated time series in CollectorRegistry:",
            ],
        )
    )


def default(
    metric_namespace: str = "",
    metric_subsystem: str = "",
    latency_highr_buckets: Sequence[float | str] = (
        0.01,
        0.025,
        0.05,
        0.075,
        0.1,
        0.25,
        0.5,
        0.75,
        1,
        1.5,
        2,
        2.5,
        3,
        3.5,
        4,
        4.5,
        5,
        7.5,
        10,
        30,
        60,
    ),
    latency_lowr_buckets: Sequence[float | str] = (0.1, 0.5, 1),
    registry: CollectorRegistry = REGISTRY,
) -> Optional[Callable[[Info], None]]:
    """Contains multiple metrics to cover multiple things.

    Combines several metrics into a single function. Also more efficient than
    multiple separate instrumentation functions that do more or less the same.

    You get the following:

    * `http_requests_total` (`handler`, `status`, `method`): Total number of
        requests by handler, status and method.
    * `http_request_size_bytes` (`handler`): Total number of incoming
        content length bytes by handler.
    * `http_response_size_bytes` (`handler`): Total number of outgoing
        content length bytes by handler.
    * `http_request_duration_highr_seconds` (no labels): High number of buckets
        leading to more accurate calculation of percentiles.
    * `http_request_duration_seconds` (`handler`, `method`):
        Kepp the bucket count very low. Only put in SLIs.

    Args:
        metric_namespace (str, optional): Namespace of all  metrics in this
            metric function. Defaults to "".

        metric_subsystem (str, optional): Subsystem of all  metrics in this
            metric function. Defaults to "".

        latency_highr_buckets (tuple[float], optional): Buckets tuple for high
            res histogram. Can be large because no labels are used. Defaults to
            (0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1, 1.5, 2, 2.5,
            3, 3.5, 4, 4.5, 5, 7.5, 10, 30, 60).

        latency_lowr_buckets (tuple[float], optional): Buckets tuple for low
            res histogram. Should be very small as all possible labels are
            included. Defaults to `(0.1, 0.5, 1)`.

    Returns:
        Function that takes a single parameter `Info`.
    """
    if latency_highr_buckets[-1] != float("inf"):
        latency_highr_buckets = [*latency_highr_buckets, float("inf")]

    if latency_lowr_buckets[-1] != float("inf"):
        latency_lowr_buckets = [*latency_lowr_buckets, float("inf")]

    # Starlette will call app.build_middleware_stack() with every new middleware
    # added, which will call all this again, which will make the registry
    # complain about duplicated metrics.
    #
    # The Python Prometheus client currently doesn't seem to have a way to
    # verify if adding a metric will cause errors or not, so the only way to
    # handle it seems to be with this try block.
    try:
        TOTAL = Counter(
            name="http_requests_total",
            documentation="Total number of requests by method, status and handler.",
            labelnames=("method", "status", "handler"),
            namespace=metric_namespace,
            subsystem=metric_subsystem,
            registry=registry,
        )

        IN_SIZE = Summary(
            name="http_request_size_bytes",
            documentation=(
                "Content length of incoming requests by handler. "
                "Only value of header is respected. Otherwise ignored. "
                "No percentile calculated. "
            ),
            labelnames=("handler",),
            namespace=metric_namespace,
            subsystem=metric_subsystem,
            registry=registry,
        )

        OUT_SIZE = Summary(
            name="http_response_size_bytes",
            documentation=(
                "Content length of outgoing responses by handler. "
                "Only value of header is respected. Otherwise ignored. "
                "No percentile calculated. "
            ),
            labelnames=("handler",),
            namespace=metric_namespace,
            subsystem=metric_subsystem,
            registry=registry,
        )

        LATENCY_HIGHR = Histogram(
            name="http_request_duration_highr_seconds",
            documentation=(
                "Latency with many buckets but no API specific labels. "
                "Made for more accurate percentile calculations. "
            ),
            buckets=latency_highr_buckets,
            namespace=metric_namespace,
            subsystem=metric_subsystem,
            registry=registry,
        )

        LATENCY_LOWR = Histogram(
            name="http_request_duration_seconds",
            documentation=(
                "Latency with only few buckets by handler. "
                "Made to be only used if aggregation by handler is important. "
            ),
            buckets=latency_lowr_buckets,
            labelnames=("method", "handler"),
            namespace=metric_namespace,
            subsystem=metric_subsystem,
            registry=registry,
        )

        def instrumentation(info: Info) -> None:
            duration = info.modified_duration

            TOTAL.labels(info.method, info.modified_status, info.modified_handler).inc()

            IN_SIZE.labels(info.modified_handler).observe(
                int(info.request.headers.get("Content-Length", 0))
            )

            if info.response and hasattr(info.response, "headers"):
                OUT_SIZE.labels(info.modified_handler).observe(
                    int(info.response.headers.get("Content-Length", 0))
                )
            else:
                OUT_SIZE.labels(info.modified_handler).observe(0)

            if info.modified_status.startswith("2"):
                LATENCY_HIGHR.observe(duration)

            LATENCY_LOWR.labels(
                handler=info.modified_handler, method=info.method
            ).observe(duration)

        return instrumentation

    except ValueError as e:
        if not _is_duplicated_time_series(e):
            raise e

    return None
