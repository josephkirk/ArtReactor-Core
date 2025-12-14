from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import time
import uuid
from artreactor.core.logging.manager import LogManager, LogLevel


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        logger = LogManager.get_instance()

        # Generate or extract trace ID
        trace_id = request.headers.get("X-Trace-ID", str(uuid.uuid4()))
        span_id = str(uuid.uuid4())  # New span for this request

        # Set context
        logger.set_context(trace_id, span_id)

        start_time = time.perf_counter()

        # Log Request
        await logger.log(
            level=LogLevel.INFO,
            message=f"Request: {request.method} {request.url.path}",
            source="api.request",
            context={
                "method": request.method,
                "url": str(request.url),
                "client": request.client.host if request.client else "unknown",
            },
        )

        try:
            response = await call_next(request)

            duration = time.perf_counter() - start_time

            # Log Response
            await logger.log(
                level=LogLevel.INFO,
                message=f"Response: {response.status_code} (Duration: {duration:.4f}s)",
                source="api.response",
                context={"status_code": response.status_code, "duration": duration},
            )

            # Inject trace ID into response headers
            response.headers["X-Trace-ID"] = trace_id

            return response

        except Exception as e:
            duration = time.perf_counter() - start_time
            await logger.log(
                level=LogLevel.ERROR,
                message=f"Request Failed: {str(e)}",
                source="api.error",
                context={"error": str(e), "duration": duration},
            )
            raise e
