from starlette.types import ASGIApp, Scope, Receive, Send
from app.main import app

class VercelPathRewriteMiddleware:
    """Restores the original client request path on Vercel serverless functions."""
    def __init__(self, asgi_app: ASGIApp):
        self.asgi_app = asgi_app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] == "http":
            headers = dict(scope.get("headers", []))
            
            # Extract candidate paths from Vercel proxy headers
            candidates = [
                headers.get(b"x-matched-path", b"").decode("utf-8"),
                headers.get(b"x-vercel-matched-path", b"").decode("utf-8"),
                headers.get(b"x-forwarded-uri", b"").decode("utf-8").split("?")[0],
                headers.get(b"x-invoke-path", b"").decode("utf-8"),
            ]
            
            resolved_path = None
            for cand in candidates:
                if cand and cand != "/api/index.py":
                    resolved_path = cand
                    break

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
