import uuid

from fastapi.testclient import TestClient

from app.main.main import app


def test_should_accept_websocket_and_close() -> None:
    client = TestClient(app)
    diagram_id = uuid.uuid4()
    with client.websocket_connect(f"/ws/diagrams/{diagram_id}") as ws:
        data = ws.receive_json()
        assert data["type"] == "connected"
        assert data["diagram_id"] == str(diagram_id)
