FROM python:3.14-slim

COPY ./dist/*.whl /tmp/
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
