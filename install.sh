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

if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env from .env.example."
fi

echo "Pulling the Ollama image..."
docker compose pull ollama

echo "Building Local LLM Node..."
docker compose build api

echo "Installation complete. Start the stack with ./run.sh"

