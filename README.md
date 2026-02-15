# Financial Monitor

A modular financial data platform for tracking government bond yield curve spreads across major economies.

## Architecture

- **Frontend**: React + Vite + TypeScript SPA (deployed to S3 + CloudFront)
- **Backend**: Python 3.12 AWS Lambda functions
- **Infrastructure**: AWS CDK v2 (TypeScript)
- **Pattern**: CQRS — DynamoDB is source of truth, S3 JSON files are read-optimized frontend views

## Project Structure

```
financial-monitor/
├── infra/                    # AWS CDK infrastructure
│   ├── bin/app.ts            # CDK app entry point
│   └── lib/stacks/           # CDK stacks
│       ├── core/             # Shared infrastructure
│       │   ├── config-stack.ts        # SSM parameters
│       │   ├── storage-cdn-stack.ts   # DynamoDB + S3 + CloudFront
│       │   └── monitoring-stack.ts    # SNS, Budgets, Kill Switch
│       └── features/         # Feature-specific stacks
│           └── bond-spreads-stack.ts
│
├── backend/                  # Python Lambda code
│   ├── shared/               # Common utilities
│   └── features/
│       └── bond_spreads/     # Bond spreads feature
│
├── frontend/                 # React SPA
│   └── src/
│       ├── features/bond-spreads/
│       └── shared/
│
└── .github/workflows/        # CI/CD (future)
```

## Quick Start

### Prerequisites

- Node.js 18+
- Python 3.12
- AWS CLI configured
- AWS CDK CLI (`npm install -g aws-cdk`)

### Deploy Infrastructure

```bash
cd infra
npm install

# Synthesize CloudFormation templates
npx cdk synth -c stage=box

# Deploy all stacks
npx cdk deploy --all -c stage=box
```

### Run Frontend Locally

```bash
cd frontend
npm install
npm run dev
```

## Features

### Bond Spreads (First Feature)

Tracks 10-year minus 3-month government bond yield spreads for:
- United States, Germany, United Kingdom, Japan, France
- Canada, Australia, Brazil, India, Mexico

**Data Sources**: FRED (Federal Reserve Economic Data)

**Update Frequency**: Monthly (1st of each month)

## Configuration

SSM Parameters (created automatically):
- `/fm/{stage}/alert-email` - Email for alerts
- `/fm/{stage}/cost-limit-warning` - Warning threshold ($10)
- `/fm/{stage}/cost-limit-critical` - Critical threshold ($15)
- `/fm/{stage}/kill-switch` - Emergency stop switch
- `/fm/{stage}/features/bond-spreads/fred-api-key` - FRED API key (update after deploy)

## License

Private
