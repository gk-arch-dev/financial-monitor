#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo "Starting LocalStack..."
docker-compose up -d

echo "Waiting for LocalStack to be ready..."
timeout 60 bash -c 'until curl -s http://localhost:4566/_localstack/health | grep -q "\"dynamodb\": \"available\""; do sleep 2; done' || {
    echo "ERROR: LocalStack failed to start within 60 seconds"
    docker-compose logs localstack
    exit 1
}

echo ""
echo "LocalStack is ready!"
echo ""
echo "Endpoints:"
echo "  All services: http://localhost:4566"
echo ""
echo "Verify resources:"
echo "  awslocal dynamodb list-tables"
echo "  awslocal s3 ls"
echo "  awslocal ssm get-parameters-by-path --path /fm/local --recursive"
echo ""
echo "Set your FRED API key:"
echo "  awslocal ssm put-parameter --name '/fm/local/features/bond-spreads/fred-api-key' --value 'YOUR_KEY' --type SecureString --overwrite"
echo ""
echo "Invoke Lambda locally:"
echo "  cd backend && python ../scripts/local-invoke.py ingest"
