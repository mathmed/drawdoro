import os

import httpx

API_URL = os.environ.get("DRAWDORO_API_URL", "http://localhost:8000")


def list_projects(workspace_id: str) -> list:
    with httpx.Client(base_url=API_URL) as client:
        response = client.get(f"/workspaces/{workspace_id}/projects")
        response.raise_for_status()
        return list(response.json())


def get_project(workspace_id: str, project_id: str) -> dict:
    with httpx.Client(base_url=API_URL) as client:
        response = client.get(f"/workspaces/{workspace_id}/projects/{project_id}")
        response.raise_for_status()
        return dict(response.json())
