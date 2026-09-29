import httpx
import pytest
from mcp.server.mcpserver.exceptions import ToolError
from tools.api import BackendApi

BASE_URL = "http://api.test"
APP_NAME = "Acme Draw"


def api_answering(response: httpx.Response) -> BackendApi:
    transport = httpx.MockTransport(lambda _: response)
    return BackendApi(httpx.Client(base_url=BASE_URL, transport=transport), APP_NAME)


def test_should_return_json_object_on_success() -> None:
    sut = api_answering(httpx.Response(200, json={"id": "abc"}))
    assert sut.get_object("/things/abc") == {"id": "abc"}


def test_should_return_json_list_on_success() -> None:
    sut = api_answering(httpx.Response(200, json=[{"id": "abc"}]))
    assert sut.get_list("/things") == [{"id": "abc"}]


def test_should_send_put_body_as_json() -> None:
    sent: list[bytes] = []

    def handler(request: httpx.Request) -> httpx.Response:
        sent.append(request.content)
        return httpx.Response(200, json={"name": "New"})

    sut = BackendApi(
        httpx.Client(base_url=BASE_URL, transport=httpx.MockTransport(handler)), APP_NAME
    )
    assert sut.put("/things/abc", {"name": "New"}) == {"name": "New"}
    assert sent == [b'{"name":"New"}']


def test_should_send_post_body_as_json() -> None:
    sent: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        sent.append(request)
        return httpx.Response(201, json={"id": "abc"})

    sut = BackendApi(
        httpx.Client(base_url=BASE_URL, transport=httpx.MockTransport(handler)), APP_NAME
    )
    assert sut.post("/things", {"name": "New"}) == {"id": "abc"}
    assert (sent[0].method, sent[0].content) == ("POST", b'{"name":"New"}')


def test_should_raise_tool_error_with_status_and_detail_on_http_error() -> None:
    sut = api_answering(httpx.Response(404, json={"detail": "Diagram abc not found"}))
    with pytest.raises(
        ToolError, match=f"{APP_NAME} API returned 404 for GET /things/abc: Diagram abc not found"
    ):
        sut.get_object("/things/abc")


def test_should_serialize_validation_errors_in_tool_error() -> None:
    detail = [{"loc": ["body", "name"], "msg": "Field required"}]
    sut = api_answering(httpx.Response(422, json={"detail": detail}))
    with pytest.raises(ToolError, match=r"422 for PUT /things: \[.*Field required"):
        sut.put("/things", {})


def test_should_use_raw_text_when_error_body_is_not_json() -> None:
    sut = api_answering(httpx.Response(502, text="Bad Gateway"))
    with pytest.raises(ToolError, match="502 for GET /things: Bad Gateway"):
        sut.get_list("/things")


def test_should_raise_tool_error_when_api_is_unreachable() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("Connection refused", request=request)

    sut = BackendApi(
        httpx.Client(base_url=BASE_URL, transport=httpx.MockTransport(handler)), APP_NAME
    )
    with pytest.raises(ToolError, match=f"Could not reach the {APP_NAME} API at {BASE_URL}"):
        sut.get_list("/things")
