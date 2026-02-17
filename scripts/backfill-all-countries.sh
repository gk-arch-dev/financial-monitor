#!/usr/bin/env bash
#
# Backfill bond spreads data for all countries in parallel
# Usage: ./scripts/backfill-all-countries.sh [start_period] [end_period]
#
# Examples:
#   ./scripts/backfill-all-countries.sh             # 10 years of data (default)
#   ./scripts/backfill-all-countries.sh 2024-01 2026-01   # Custom range
#

set -e

# Configuration
FUNCTION_NAME="fm-box-bond-spreads-backfill"
COUNTRIES=("US" "DE" "GB" "JP" "IN" "BR" "FR" "CA" "AU")
START_PERIOD="${1:-}"  # Optional: YYYY-MM
END_PERIOD="${2:-}"    # Optional: YYYY-MM

echo "=================================="
echo "Bond Spreads Backfill - All Countries"
echo "=================================="
echo "Function: $FUNCTION_NAME"
echo "Countries: ${COUNTRIES[*]}"
if [ -n "$START_PERIOD" ] && [ -n "$END_PERIOD" ]; then
  echo "Period: $START_PERIOD to $END_PERIOD"
else
  echo "Period: Last 10 years (default)"
fi
echo "=================================="
echo

# Build payload
if [ -n "$START_PERIOD" ] && [ -n "$END_PERIOD" ]; then
  PAYLOAD_TEMPLATE='{"country":"%s","start_period":"'"$START_PERIOD"'","end_period":"'"$END_PERIOD"'"}'
else
  PAYLOAD_TEMPLATE='{"country":"%s"}'
fi

# Array to store background job PIDs
declare -a PIDS=()
declare -a OUTPUTS=()

# Invoke Lambda for each country in parallel
for COUNTRY in "${COUNTRIES[@]}"; do
  OUTPUT_FILE="/tmp/backfill-${COUNTRY}.json"
  OUTPUTS+=("$OUTPUT_FILE")

  PAYLOAD=$(printf "$PAYLOAD_TEMPLATE" "$COUNTRY")

  echo "[$COUNTRY] Starting backfill..."

  aws lambda invoke \
    --function-name "$FUNCTION_NAME" \
    --payload "$PAYLOAD" \
    --cli-binary-format raw-in-base64-out \
    "$OUTPUT_FILE" \
    > /dev/null 2>&1 &

  PIDS+=($!)
done

echo
echo "All Lambda invocations started. Waiting for completion..."
echo

# Wait for all background jobs and collect results
SUCCESS_COUNT=0
FAILED_COUNT=0
declare -a FAILED_COUNTRIES=()

for i in "${!PIDS[@]}"; do
  PID="${PIDS[$i]}"
  COUNTRY="${COUNTRIES[$i]}"
  OUTPUT_FILE="${OUTPUTS[$i]}"

  if wait "$PID"; then
    if [ -f "$OUTPUT_FILE" ]; then
      STATUS=$(cat "$OUTPUT_FILE" | grep -o '"statusCode":[0-9]*' | cut -d':' -f2 || echo "unknown")
      if [ "$STATUS" = "200" ]; then
        echo "✅ [$COUNTRY] Success"
        ((SUCCESS_COUNT++))
      else
        echo "❌ [$COUNTRY] Failed (status: $STATUS)"
        ((FAILED_COUNT++))
        FAILED_COUNTRIES+=("$COUNTRY")
      fi
    else
      echo "❌ [$COUNTRY] No response file"
      ((FAILED_COUNT++))
      FAILED_COUNTRIES+=("$COUNTRY")
    fi
  else
    echo "❌ [$COUNTRY] Lambda invocation failed"
    ((FAILED_COUNT++))
    FAILED_COUNTRIES+=("$COUNTRY")
  fi
done

echo
echo "=================================="
echo "Backfill Summary"
echo "=================================="
echo "✅ Success: $SUCCESS_COUNT"
echo "❌ Failed: $FAILED_COUNT"
if [ ${#FAILED_COUNTRIES[@]} -gt 0 ]; then
  echo "Failed countries: ${FAILED_COUNTRIES[*]}"
fi
echo "=================================="
echo

# Generate JSON files if all countries succeeded
if [ $FAILED_COUNT -eq 0 ]; then
  echo "🎉 All countries completed successfully!"
  echo "Now generating JSON files..."
  echo

  # Invoke backfill Lambda with generate_json flag (no country specified = all countries)
  if [ -n "$START_PERIOD" ] && [ -n "$END_PERIOD" ]; then
    JSON_PAYLOAD='{"generate_json":true,"start_period":"'"$START_PERIOD"'","end_period":"'"$END_PERIOD"'"}'
  else
    JSON_PAYLOAD='{"generate_json":true}'
  fi

  aws lambda invoke \
    --function-name "$FUNCTION_NAME" \
    --payload "$JSON_PAYLOAD" \
    --cli-binary-format raw-in-base64-out \
    /tmp/backfill-json.json

  echo
  echo "✅ JSON files generated and uploaded to S3!"
  echo "CloudFront cache invalidation triggered (may take 5-10 minutes to propagate)"
  echo
  exit 0
else
  echo "⚠️  Some countries failed. Skipping JSON generation."
  echo "Fix the failed countries and run again."
  exit 1
fi
