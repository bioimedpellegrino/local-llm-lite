#!/bin/sh

set -eu

project_directory=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$project_directory"

if ! command -v docker >/dev/null 2>&1; then
    echo "Error: Docker is not installed or is not available in PATH." >&2
    exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
    echo "Error: the Docker Compose plugin is not available." >&2
    exit 1
fi

if ! docker info >/dev/null 2>&1; then
    echo "Error: the Docker daemon is not running or is not accessible." >&2
    exit 1
fi

if [ "${1:-}" = "--nvidia" ]; then
    shift
    exec docker compose \
        -f compose.yaml \
        -f compose.nvidia.yaml \
        up --build "$@"
fi

exec docker compose up --build "$@"

