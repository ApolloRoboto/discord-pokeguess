set windows-shell := ["powershell.exe", "-c"]

[private]
default:
    @just --list --unsorted

[unix]
init:
    uv sync --all-extras
    test ! -e ".env" && cp "example.env" ".env"

[windows]
init:
    uv sync --all-extras
    if (!(Test-Path ".env")) {Copy-Item "example.env" ".env"}

build:
    uv build

run:
    uv run main

test:
    uv run pytest

check:
    uv run ty check
    uv run ruff check

[unix]
clean:
    find . -type d -name "__pycache__" -exec rm -rf {} +
    rm -rf .ruff_cache dist .venv

[windows]
clean:
    Get-ChildItem -Path . -Directory -Recurse -Filter "__pycache__" | Remove-Item -Recurse -Force
    if (Test-Path ".ruff_cache") {Remove-Item -Recurse -Force ".ruff_cache"}
    if (Test-Path "dist") {Remove-Item -Recurse -Force "dist"}
    if (Test-Path ".venv") {Remove-Item -Recurse -Force ".venv"}

dockerbuild: build
    docker compose build

dockerrun:
    docker compose up
