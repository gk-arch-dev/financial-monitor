#!/bin/bash
set -euo pipefail

echo "=== Initializing LocalStack resources for Financial Monitor ==="

REGION="eu-central-1"
STAGE="local"
TABLE_NAME="fm-${STAGE}-data"
BUCKET_NAME="fm-${STAGE}-frontend"
SSM_PREFIX="/fm/${STAGE}"

# Create DynamoDB table with GSI
echo "Creating DynamoDB table: ${TABLE_NAME}"
awslocal dynamodb create-table \
    --table-name "${TABLE_NAME}" \
    --attribute-definitions \
        AttributeName=PK,AttributeType=S \
        AttributeName=SK,AttributeType=S \
        AttributeName=GSI1PK,AttributeType=S \
        AttributeName=GSI1SK,AttributeType=N \
    --key-schema \
        AttributeName=PK,KeyType=HASH \
        AttributeName=SK,KeyType=RANGE \
    --global-secondary-indexes \
        '[{
            "IndexName": "GSI1",
            "KeySchema": [
                {"AttributeName": "GSI1PK", "KeyType": "HASH"},
                {"AttributeName": "GSI1SK", "KeyType": "RANGE"}
            ],
            "Projection": {"ProjectionType": "ALL"}
        }]' \
    --billing-mode PAY_PER_REQUEST \
    --region "${REGION}" 2>/dev/null || echo "Table may already exist"

# Create S3 bucket
echo "Creating S3 bucket: ${BUCKET_NAME}"
awslocal s3 mb "s3://${BUCKET_NAME}" --region "${REGION}" 2>/dev/null || echo "Bucket may already exist"

# Enable CORS on S3 bucket for local frontend
echo "Configuring CORS for S3 bucket"
awslocal s3api put-bucket-cors \
    --bucket "${BUCKET_NAME}" \
    --cors-configuration '{
        "CORSRules": [{
            "AllowedHeaders": ["*"],
            "AllowedMethods": ["GET", "HEAD"],
            "AllowedOrigins": ["http://localhost:5173", "http://localhost:3000"],
            "ExposeHeaders": []
        }]
    }' --region "${REGION}"

# Create SSM parameters
echo "Creating SSM parameters"
awslocal ssm put-parameter \
    --name "${SSM_PREFIX}/kill-switch" \
    --value "false" \
    --type String \
    --region "${REGION}" \
    --overwrite 2>/dev/null || true

awslocal ssm put-parameter \
    --name "${SSM_PREFIX}/features/bond-spreads/fred-api-key" \
    --value "REPLACE_WITH_YOUR_FRED_API_KEY" \
    --type SecureString \
    --region "${REGION}" \
    --overwrite 2>/dev/null || true

awslocal ssm put-parameter \
    --name "${SSM_PREFIX}/alert-email" \
    --value "local@example.com" \
    --type String \
    --region "${REGION}" \
    --overwrite 2>/dev/null || true

# Seed sample data if seed file exists
SEED_FILE="/etc/localstack/init/seed/bond-spreads-sample.json"
if [ -f "${SEED_FILE}" ]; then
    echo "Seeding sample bond spreads data to S3"
    awslocal s3 cp "${SEED_FILE}" "s3://${BUCKET_NAME}/data/bond-spreads/spreads-latest.json" \
        --content-type "application/json" \
        --region "${REGION}"
fi

echo "=== LocalStack initialization complete ==="
echo "DynamoDB Table: ${TABLE_NAME}"
echo "S3 Bucket: ${BUCKET_NAME}"
echo "SSM Prefix: ${SSM_PREFIX}"
echo ""
echo "To set your FRED API key, run:"
echo "  awslocal ssm put-parameter --name '${SSM_PREFIX}/features/bond-spreads/fred-api-key' --value 'YOUR_KEY' --type SecureString --overwrite"
