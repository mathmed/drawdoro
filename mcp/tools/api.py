import json
from enum import StrEnum
from typing import Any, cast

import httpx
from mcp.server.mcpserver.exceptions import ToolError

JsonObject = dict[str, Any]


class HttpMethod(StrEnum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"


class DrawdoroApi:
    def __init__(self, client: httpx.Client) -> None:
        self._client = client

    def get_object(self, path: str) -> JsonObject:
        return cast(JsonObject, self._request(HttpMethod.GET, path).json())

    def get_list(self, path: str) -> list[JsonObject]:
        return cast(list[JsonObject], self._request(HttpMethod.GET, path).json())

    def post(self, path: str, body: JsonObject) -> JsonObject:
        return cast(JsonObject, self._request(HttpMethod.POST, path, body).json())

    def put(self, path: str, body: JsonObject) -> JsonObject:
        return cast(JsonObject, self._request(HttpMethod.PUT, path, body).json())

    def _request(
        self, method: HttpMethod, path: str, body: JsonObject | None = None
    ) -> httpx.Response:
        # ToolError is the only exception whose message reaches the model; anything else is masked.
        try:
            response = self._client.request(method, path, json=body)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            detail = _error_detail(exc.response)
            raise ToolError(
                f"Drawdoro API returned {status} for {method} {path}: {detail}"
            ) from exc
        except httpx.RequestError as exc:
            raise ToolError(
                f"Could not reach the Drawdoro API at {self._client.base_url}: {exc}"
            ) from exc
        return response


def _error_detail(response: httpx.Response) -> str:
    try:
        body = response.json()
    except ValueError:
        return response.text
    detail = body.get("detail", body) if isinstance(body, dict) else body
    return detail if isinstance(detail, str) else json.dumps(detail)
