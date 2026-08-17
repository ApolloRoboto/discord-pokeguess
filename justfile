set windows-shell := ["powershell.exe", "-c"]

[private]
default:
    @just --list --unsorted

init:
    uv sync --all-extras

build:
    uv build

run:
    uv run main

check:
    uv run ruff check
    uv run ty check

dockerbuild: build
    docker compose build

dockerrun:
    docker compose up
