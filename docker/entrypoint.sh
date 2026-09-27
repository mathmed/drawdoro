#!/bin/bash

cd /home/app
uv sync
uv run alembic upgrade head
uv run uvicorn app.main.main:app --host=0.0.0.0 --port=8000 --reload
