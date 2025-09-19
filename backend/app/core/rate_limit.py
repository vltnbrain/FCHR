import time
from typing import Callable, Awaitable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, limit_per_minute: int = 120):
        super().__init__(app)
        self.limit = limit_per_minute
        self.window = 60
        self.store: dict[str, list[float]] = {}

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]):
        key = self._key(request)
        now = time.time()
        hits = self.store.get(key, [])
        # prune
        cutoff = now - self.window
        hits = [t for t in hits if t > cutoff]
        if len(hits) >= self.limit:
            retry_after = max(1, int(hits[0] + self.window - now))
            return JSONResponse({"detail": "Too Many Requests"}, status_code=429, headers={"Retry-After": str(retry_after)})
        hits.append(now)
        self.store[key] = hits
        return await call_next(request)

    def _key(self, request: Request) -> str:
        xff = request.headers.get("x-forwarded-for")
        ip = xff.split(",")[0].strip() if xff else request.client.host
        path = request.url.path.split("/")[1] if request.url.path else "root"
        return f"{ip}:{path}"

