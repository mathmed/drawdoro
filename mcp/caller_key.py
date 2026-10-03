from contextvars import ContextVar
from typing import Any

from mcp.server.context import CallNext, HandlerResult, ServerRequestContext

BEARER_PREFIX = "bearer "

# The API key sent by whoever called this MCP server over HTTP: with a personal key, their agent
# acts as them and shows up as "Claude of <name>". Unset over stdio or when no key is sent, and
# then the server's own key (MCP_API_KEY) is used.
caller_api_key: ContextVar[str | None] = ContextVar("caller_api_key", default=None)


def api_key_from_headers(headers: Any) -> str | None:
    if headers is None:
        return None
    return header_api_key(headers) or bearer_token(headers)


def header_api_key(headers: Any) -> str | None:
    key = (headers.get("x-api-key") or "").strip()
    return str(key) if key else None


def bearer_token(headers: Any) -> str | None:
    authorization = (headers.get("authorization") or "").strip()
    if not authorization.lower().startswith(BEARER_PREFIX):
        return None
    return authorization[len(BEARER_PREFIX) :].strip() or None


class ForwardCallerApiKey:
    async def __call__(
        self, ctx: ServerRequestContext[Any, Any], call_next: CallNext
    ) -> HandlerResult:
        key = api_key_from_headers(getattr(ctx.request, "headers", None))
        token = caller_api_key.set(key)
        try:
            return await call_next(ctx)
        finally:
            caller_api_key.reset(token)
