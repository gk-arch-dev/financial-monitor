# Backend - Financial Monitor

Python backend code for AWS Lambda functions.

## Directory Structure

```
backend/
├── features/              # Feature-specific Lambda handlers
│   └── bond_spreads/     # Bond spreads feature
│       ├── handlers/     # Lambda function handlers
│       ├── models/       # Data models and types
│       ├── services/     # Business logic and external API clients
│       └── tests/        # Feature-specific tests
├── shared/               # Shared utilities across features
├── lambda-layer/         # Lambda Layer dependencies (NOT in Git)
│   └── python/          # Installed Python packages
├── requirements.txt      # Python dependencies
└── build-layer.sh       # Script to build Lambda Layer
```

## Setup

### 1. Build Lambda Layer

The Lambda Layer contains all Python dependencies and is deployed separately from the Lambda code.

**Important:** The `lambda-layer/` directory is **NOT tracked in Git** (like `node_modules/`).

Build the layer before deploying:

```bash
cd backend
./build-layer.sh
```

This installs all packages from `requirements.txt` into `lambda-layer/python/` with Linux-compatible binaries for AWS Lambda.

### 2. Install Dev Dependencies (Optional)

For local development and testing:

```bash
pip install -r requirements.txt
```

## Dependencies

### Production (Lambda)
- `boto3` - AWS SDK
- `aws-lambda-powertools` - Logging, tracing, metrics
- `requests` - HTTP client for FRED API
- `python-dateutil` - Date utilities

### Development/Testing Only
- `pytest` - Testing framework
- `pytest-mock` - Mocking utilities
- `moto` - AWS service mocking

**Note:** Test dependencies should ideally be in a separate `requirements-dev.txt` to reduce Lambda layer size.

## Running Tests

```bash
cd backend
pytest
```

## Deployment

The CDK stack (`infra/lib/stacks/features/bond-spreads-stack.ts`) automatically:
1. Packages Lambda Layer from `lambda-layer/` directory
2. Packages Lambda function code (excluding `lambda-layer/`, `tests/`, etc.)
3. Deploys both to AWS

## Adding New Dependencies

1. Add to `requirements.txt`
2. Rebuild layer: `./build-layer.sh`
3. Deploy: `cd ../infra && npx cdk deploy`
