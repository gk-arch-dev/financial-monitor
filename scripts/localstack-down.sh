#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo "Stopping LocalStack..."
docker-compose down

echo "LocalStack stopped."
echo ""
echo "Note: LocalStack data is persisted in ./localstack/data/"
echo "To clean up data, run: rm -rf ./localstack/data/"
