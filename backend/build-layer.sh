#!/bin/bash
# Build Lambda Layer from requirements.txt
# This script installs Python dependencies into the lambda-layer directory
# for deployment to AWS Lambda

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LAYER_DIR="$SCRIPT_DIR/lambda-layer/python"

echo "Building Lambda Layer..."
echo "Target directory: $LAYER_DIR"

# Clean existing layer
if [ -d "$LAYER_DIR" ]; then
    echo "Removing existing layer..."
    rm -rf "$LAYER_DIR"
fi

# Create layer directory
mkdir -p "$LAYER_DIR"

# Install dependencies
echo "Installing dependencies from requirements.txt..."
pip install \
    --target "$LAYER_DIR" \
    --platform manylinux2014_x86_64 \
    --implementation cp \
    --python-version 3.12 \
    --only-binary=:all: \
    --upgrade \
    -r "$SCRIPT_DIR/requirements.txt"

echo "✓ Lambda layer built successfully!"
echo "Location: $LAYER_DIR"
echo ""
echo "Files installed:"
ls -lh "$LAYER_DIR" | wc -l
echo "Total size:"
du -sh "$LAYER_DIR"
