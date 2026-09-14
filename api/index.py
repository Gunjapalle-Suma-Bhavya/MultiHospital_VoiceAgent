from app.main import app
from starlette.types import ASGIApp, Scope, Receive, Send

class VercelPathRewriteMiddleware:
    """Restores the original client request path on Vercel serverless functions."""
    def __init__(self, asgi_app: ASGIApp):
        self.asgi_app = asgi_app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] == "http":
            headers = dict(scope.get("headers", []))
            forwarded_uri = headers.get(b"x-forwarded-uri", b"").decode("utf-8")
            matched_path = headers.get(b"x-matched-path", b"").decode("utf-8")
            raw_path = scope.get("path", "")

            if forwarded_uri:
                clean_path = forwarded_uri.split("?")[0]
                scope["path"] = clean_path
                scope["raw_path"] = clean_path.encode("utf-8")
            elif matched_path and matched_path != "/api/index.py":
                scope["path"] = matched_path
                scope["raw_path"] = matched_path.encode("utf-8")
            elif raw_path.startswith("/api/index.py"):
                subpath = raw_path[len("/api/index.py"):]
                clean_path = subpath if subpath.startswith("/") else ("/" + subpath if subpath else "/")
                scope["path"] = clean_path
                scope["raw_path"] = clean_path.encode("utf-8")
            elif raw_path in ("/api", "/api/"):
                scope["path"] = "/"
                scope["raw_path"] = b"/"

        await self.asgi_app(scope, receive, send)

app = VercelPathRewriteMiddleware(app)
