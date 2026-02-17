#!/usr/bin/env bash
#
# Generate JSON files from existing DynamoDB data (no backfill)
# Usage: ./scripts/generate-json-files.sh
#

set -e

FUNCTION_NAME="fm-box-bond-spreads-backfill"

echo "=================================="
echo "Generating JSON files from DynamoDB"
echo "=================================="
echo "Function: $FUNCTION_NAME"
echo

# Invoke backfill Lambda with generate_json flag only
# This skips data fetching and just generates JSON from existing DynamoDB data
PAYLOAD='{"generate_json":true}'

aws lambda invoke \
  --function-name "$FUNCTION_NAME" \
  --payload "$PAYLOAD" \
  --cli-binary-format raw-in-base64-out \
  /tmp/generate-json.json

echo
echo "Response:"
cat /tmp/generate-json.json | python3 -m json.tool 2>/dev/null || cat /tmp/generate-json.json
echo

# Check if S3 files exist
echo
echo "Checking S3 files..."
aws s3 ls s3://fm-box-frontend-363210543697/data/bond-spreads/

echo
echo "✅ JSON generation complete!"
echo "Files should be available at: https://dpdhq4a9oxtjl.cloudfront.net/data/bond-spreads/"
echo "Note: CloudFront cache invalidation may take 5-10 minutes to propagate"
