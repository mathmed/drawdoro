import os

import httpx

API_URL = os.environ.get("DRAWDORO_API_URL", "http://localhost:8000")


def get_diagram(project_id: str, diagram_id: str) -> dict:
    with httpx.Client(base_url=API_URL) as client:
        response = client.get(f"/projects/{project_id}/diagrams/{diagram_id}")
        response.raise_for_status()
        return dict(response.json())


def update_diagram(project_id: str, diagram_id: str, payload: dict) -> dict:
    with httpx.Client(base_url=API_URL) as client:
        response = client.put(f"/projects/{project_id}/diagrams/{diagram_id}", json=payload)
        response.raise_for_status()
        return dict(response.json())


def list_diagrams(project_id: str) -> list:
    with httpx.Client(base_url=API_URL) as client:
        response = client.get(f"/projects/{project_id}/diagrams")
        response.raise_for_status()
        return list(response.json())
