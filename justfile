set windows-shell := ["powershell.exe", "-c"]

[private]
default:
    @just --list --unsorted

build:
    uv build

run:
    uv run main

check:
    ruff check
    ty check

dockerbuild: build
    docker compose build

dockerrun:
    docker compose up
