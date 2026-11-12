#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

IMAGE_NAME="${NZILA_IMAGE_NAME:-open-webui:nzila-custom}"
BUILD_HASH="${NZILA_BUILD_HASH:-$(git rev-parse --short HEAD 2>/dev/null || echo nzila-custom)}"
BUILD_CHANNEL="${NZILA_BUILD_CHANNEL:-nzila-custom}"

echo "Building ${IMAGE_NAME} (hash=${BUILD_HASH}, channel=${BUILD_CHANNEL})"

docker build \
  --build-arg "BUILD_HASH=${BUILD_HASH}" \
  --build-arg "BUILD_CHANNEL=${BUILD_CHANNEL}" \
  -t "${IMAGE_NAME}" \
  .

echo "Built ${IMAGE_NAME}"
