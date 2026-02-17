#!/usr/bin/env bash
#
# Backfill bond spreads - invoke Lambda once per country
#

set -e

FUNCTION_NAME="fm-box-bond-spreads-backfill"
COUNTRIES=("US" "DE" "GB" "JP" "IN" "BR" "FR" "CA" "AU")

echo "Starting backfill for ${#COUNTRIES[@]} countries..."
echo

# Invoke Lambda for each country in parallel
for COUNTRY in "${COUNTRIES[@]}"; do
  echo "[$COUNTRY] Invoking Lambda..."

  aws lambda invoke \
    --function-name "$FUNCTION_NAME" \
    --payload "{\"country\":\"$COUNTRY\"}" \
    --cli-binary-format raw-in-base64-out \
    "/tmp/backfill-$COUNTRY.json" \
    > /dev/null 2>&1 &
done

echo
echo "All Lambda invocations started. Each country processes independently."
echo "Check logs: aws logs tail /aws/lambda/$FUNCTION_NAME --follow"
