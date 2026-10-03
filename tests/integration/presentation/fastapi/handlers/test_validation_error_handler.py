from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx2 import Response
from pydantic import BaseModel, Field
from pytest import fixture, mark

from app.presentation.fastapi.handlers.domain_error_handler import register_error_handlers


class Point(BaseModel):
    x: float = Field(allow_inf_nan=False)
    tags: list[float] = Field(default=[], max_length=1)


@fixture
def client() -> TestClient:
    app = FastAPI()
    register_error_handlers(app)

    @app.post("/points")
    async def create_point(point: Point) -> Point:
        return point

    return TestClient(app, raise_server_exceptions=False)


# Python reads NaN and Infinity in JSON, but httpx refuses to write them: the body is raw text.
def post(client: TestClient, body: str) -> Response:
    return client.post("/points", content=body, headers={"Content-Type": "application/json"})


@mark.parametrize(("raw", "echoed"), [("NaN", "nan"), ("Infinity", "inf"), ("-Infinity", "-inf")])
def test_should_answer_422_when_the_input_has_numbers_json_cannot_hold(
    client: TestClient, raw: str, echoed: str
) -> None:
    response = post(client, f'{{"x": {raw}}}')

    assert response.status_code == 422
    [error] = response.json()["detail"]
    assert (error["loc"], error["input"]) == (["body", "x"], echoed)


def test_should_make_numbers_inside_echoed_lists_and_objects_safe(client: TestClient) -> None:
    response = post(client, '{"x": 1, "tags": [NaN, 2]}')

    assert response.status_code == 422
    [error] = response.json()["detail"]
    assert error["input"] == ["nan", 2]


# A missing field echoes the whole body, so the numbers are made safe inside objects too.
def test_should_make_numbers_inside_echoed_objects_safe(client: TestClient) -> None:
    response = post(client, '{"y": {"z": [Infinity, 1.5, "a", true, null]}}')

    assert response.status_code == 422
    [error] = response.json()["detail"]
    assert (error["type"], error["input"]) == (
        "missing",
        {"y": {"z": ["inf", 1.5, "a", True, None]}},
    )


def test_should_keep_fastapis_answer_for_other_inputs(client: TestClient) -> None:
    response = client.post("/points", json={"x": "far"})

    assert response.status_code == 422
    [error] = response.json()["detail"]
    assert (error["type"], error["loc"], error["input"]) == ("float_parsing", ["body", "x"], "far")
