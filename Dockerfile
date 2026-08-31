# inspired from:
# https://docs.astral.sh/uv/guides/integration/docker/#non-editable-installs


FROM python:3.14-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
ENV UV_PYTHON_DOWNLOADS=0

WORKDIR /src

COPY . /src

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-editable

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-editable

RUN --mount=type=cache,target=/root/.cache/uv \
    uv build --wheel -o dist

FROM python:3.14-slim

COPY --from=builder /src/dist/*.whl /tmp/
COPY ./resources/ /app/resources/

RUN pip install --no-cache-dir /tmp/*.whl && \
    rm -f /tmp/*.whl

RUN groupadd -g 1000 app_group && \
    useradd -m -u 1000 --gid app_group app_user

COPY <<'EOF' /entrypoint.sh
#!/bin/sh
set -e
chown -R app_user:app_group /app/pokemons
exec su app_user -c "exec $*"
EOF

RUN chmod +x /entrypoint.sh

WORKDIR /app

ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "-m", "pokeguess"]
