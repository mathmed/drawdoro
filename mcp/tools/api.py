import json
from enum import StrEnum
from typing import Any, cast

import httpx
from caller_key import caller_api_key
from mcp.server.mcpserver.exceptions import ToolError

JsonObject = dict[str, Any]


class HttpMethod(StrEnum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"


class BackendApi:
    def __init__(self, client: httpx.Client, app_name: str) -> None:
        self._client = client
        self._app_name = app_name

    def get_object(self, path: str) -> JsonObject:
        return cast(JsonObject, self._request(HttpMethod.GET, path).json())

    def get_list(self, path: str) -> list[JsonObject]:
        return cast(list[JsonObject], self._request(HttpMethod.GET, path).json())

    def post(self, path: str, body: JsonObject) -> JsonObject:
        return cast(JsonObject, self._request(HttpMethod.POST, path, body).json())

    def put(self, path: str, body: JsonObject) -> JsonObject:
        return cast(JsonObject, self._request(HttpMethod.PUT, path, body).json())

    def patch(self, path: str, body: JsonObject) -> JsonObject:
        return cast(JsonObject, self._request(HttpMethod.PATCH, path, body).json())

    # Deletions answer 204 without a body.
    def delete(self, path: str) -> None:
        self._request(HttpMethod.DELETE, path)

    def _request(
        self, method: HttpMethod, path: str, body: JsonObject | None = None
    ) -> httpx.Response:
        # ToolError is the only exception whose message reaches the model; anything else is masked.
        try:
            response = self._client.request(method, path, json=body, headers=_caller_headers())
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            detail = _error_detail(exc.response)
            raise ToolError(
                f"{self._app_name} API returned {status} for {method} {path}: {detail}"
            ) from exc
        except httpx.RequestError as exc:
            raise ToolError(
                f"Could not reach the {self._app_name} API at {self._client.base_url}: {exc}"
            ) from exc
        return response


def _caller_headers() -> dict[str, str]:
    key = caller_api_key.get()
    return {"X-API-Key": key} if key else {}


def _error_detail(response: httpx.Response) -> str:
    try:
        body = response.json()
    except ValueError:
        return response.text
    detail = body.get("detail", body) if isinstance(body, dict) else body
    return detail if isinstance(detail, str) else json.dumps(detail)
