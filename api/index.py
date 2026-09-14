from starlette.types import ASGIApp, Scope, Receive, Send
from urllib.parse import parse_qs, urlencode
from app.main import app

class VercelPathRewriteMiddleware:
    """Restores the original client request path on Vercel serverless functions."""
    def __init__(self, asgi_app: ASGIApp):
        self.asgi_app = asgi_app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] == "http":
            headers = dict(scope.get("headers", []))
            
            # 1. Extract candidate paths from standard Vercel proxy headers
            candidates = [
                headers.get(b"x-matched-path", b"").decode("utf-8"),
                headers.get(b"x-vercel-matched-path", b"").decode("utf-8"),
                headers.get(b"x-forwarded-uri", b"").decode("utf-8").split("?")[0],
                headers.get(b"x-invoke-path", b"").decode("utf-8"),
                headers.get(b"x-original-url", b"").decode("utf-8").split("?")[0],
                headers.get(b"x-rewrite-url", b"").decode("utf-8").split("?")[0],
            ]
            
            resolved_path = None
            for cand in candidates:
                if cand and cand != "/api/index.py" and not cand.startswith("/index."):
                    resolved_path = cand
                    break

            # 2. Check fallback query parameter passed via vercel.json rewrite
            raw_qs = scope.get("query_string", b"").decode("utf-8")
            if "_vercel_path" in raw_qs:
                try:
                    parsed_qs = parse_qs(raw_qs)
                    if "_vercel_path" in parsed_qs:
                        fallback_path = parsed_qs.pop("_vercel_path")[0]
                        if not resolved_path or resolved_path == "/api/index.py":
                            resolved_path = fallback_path
                        # Clean query string for underlying FastAPI route handlers
                        scope["query_string"] = urlencode(parsed_qs, doseq=True).encode("utf-8")
                except Exception:
                    pass

            raw_path = scope.get("path", "")
            if resolved_path:
                scope["path"] = resolved_path
                scope["raw_path"] = resolved_path.encode("utf-8")
            elif raw_path.startswith("/api/index.py"):
                subpath = raw_path[len("/api/index.py"):]
                clean_path = subpath if subpath.startswith("/") else ("/" + subpath if subpath else "/")
                scope["path"] = clean_path
                scope["raw_path"] = clean_path.encode("utf-8")

        await self.asgi_app(scope, receive, send)

app = VercelPathRewriteMiddleware(app)
