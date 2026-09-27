import uuid

from fastapi.testclient import TestClient

from app.main.main import app


def test_should_send_peer_count_on_connect() -> None:
    client = TestClient(app)
    diagram_id = uuid.uuid4()
    with client.websocket_connect(f"/ws/diagrams/{diagram_id}") as ws:
        data = ws.receive_json()
        assert data["type"] == "peers"
        assert data["peers"] == 1


def test_should_keep_socket_open_after_update_without_peers() -> None:
    client = TestClient(app)
    diagram_id = uuid.uuid4()
    with client.websocket_connect(f"/ws/diagrams/{diagram_id}") as ws:
        assert ws.receive_json()["type"] == "peers"
        # With no other peers connected, updates are simply not echoed back and
        # the socket stays healthy.
        ws.send_json({"type": "update", "client_id": "solo", "snapshot": {}})
        ws.send_json({"type": "cursor", "client_id": "solo", "x": 1, "y": 2})
