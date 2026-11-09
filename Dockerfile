# syntax=docker/dockerfile:1

# uv の実行ファイルだけを取り出すためのステージです。
FROM ghcr.io/astral-sh/uv:0.13.7@sha256:96f40d3904aad8d0bd010539001d36c8e2188b981e1334471a90c4a1d93bb490 AS uv

# uv.lock どおりに依存とプロジェクトを仮想環境へインストールするステージです。
FROM python:3.15-slim@sha256:65a65fc7b30b06cb6df4930fd4650697cb23f4c2698ab81fc87e4b031bc36928 AS builder
COPY --from=uv /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_NO_CACHE=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/opt/venv
WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --locked --no-dev --no-install-project
COPY src ./src
RUN uv sync --locked --no-dev --no-editable

# 実行用ステージです。仮想環境だけをコピーし、非 root ユーザーで実行します。
FROM python:3.15-slim@sha256:65a65fc7b30b06cb6df4930fd4650697cb23f4c2698ab81fc87e4b031bc36928 AS runtime
# ベースイメージにまだ取り込まれていない Debian のセキュリティ更新を適用します。
RUN apt-get update \
    && apt-get upgrade -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system --gid 10001 slalog \
    && useradd --system --uid 10001 --gid slalog --no-create-home --shell /usr/sbin/nologin slalog
COPY --from=builder /opt/venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SLALOG_LOGS_DIR=/logs
USER 10001:10001
WORKDIR /logs
ENTRYPOINT ["slalog"]
CMD ["--help"]
