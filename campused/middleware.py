import time

from prometheus_client import Counter, Histogram

REQUEST_COUNT = Counter(
    "http_requests_total", "Total number of requests", ["method", "endpoint", "status_code"]
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds", "Request latency", ["method", "endpoint"]
)

class PrometheusMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.time()
        response = self.get_response(request)
        duration = time.time() - start
        endpoint = request.path
        REQUEST_COUNT.labels(request.method, endpoint, response.status_code).inc()
        REQUEST_LATENCY.labels(request.method, endpoint).observe(duration)
        return response
