# Step 0: Project Scaffolding & CDK Infrastructure

## Context
We're building **Financial Monitor** — a modular financial data platform. The first feature is **Bond Spreads** (government bond yield curve spreads, 10Y minus 3M, for major economies). The architecture supports adding more features later (e.g., currency rates, equity indices, commodities).

Full architecture:
- **Frontend**: React + Vite + TypeScript + TanStack React Query (static SPA on S3 + CloudFront)
- **Backend**: Python 3.12 Lambdas, organized by feature module
- **Infra**: AWS CDK (TypeScript), no SAM
- **Pattern**: CQRS — DynamoDB is source of truth, S3 JSON files are read-optimized frontend view
- **No API Gateway** — frontend fetches static `/data/{feature}/*.json` from CloudFront

## Task

Create the monorepo structure and deploy all CDK infrastructure (empty Lambdas, just the scaffolding).

## Monorepo Structure

```
financial-monitor/
├── infra/                              # CDK (TypeScript)
│   ├── bin/
│   │   └── app.ts                      # CDK app entry point
│   ├── lib/
│   │   ├── stacks/
│   │   │   ├── core/                   # Shared platform infrastructure
│   │   │   │   ├── storage-stack.ts    # DynamoDB, S3
│   │   │   │   ├── cdn-stack.ts        # CloudFront
│   │   │   │   ├── monitoring-stack.ts # Budgets, alarms, SNS, kill switch
│   │   │   │   └── config-stack.ts     # SSM parameters
│   │   │   └── features/
│   │   │       └── bond-spreads-stack.ts  # Lambdas + EventBridge for bond spreads feature
│   │   └── constructs/                 # Reusable CDK constructs
│   ├── cdk.json
│   ├── tsconfig.json
│   └── package.json
│
├── backend/                            # Python 3.12
│   ├── shared/                         # Shared utilities across features
│   │   ├── __init__.py
│   │   ├── dynamo_service.py           # Generic DynamoDB operations
│   │   ├── s3_publisher.py             # Generic S3 upload + CF invalidation
│   │   ├── ssm_utils.py                # SSM parameter reading, kill switch check
│   │   └── models.py                   # Base dataclasses
│   ├── features/
│   │   └── bond_spreads/               # First feature module
│   │       ├── __init__.py
│   │       ├── handlers/
│   │       │   ├── __init__.py
│   │       │   ├── ingest.py           # placeholder: def handler(event, context): pass
│   │       │   └── backfill.py         # placeholder: def handler(event, context): pass
│   │       ├── services/
│   │       │   ├── __init__.py
│   │       │   ├── fred_client.py
│   │       │   ├── spread_calculator.py
│   │       │   ├── json_generator.py
│   │       │   └── config.py           # Country/series ID map
│   │       ├── models/
│   │       │   ├── __init__.py
│   │       │   └── types.py
│   │       └── tests/
│   │           └── __init__.py
│   ├── tests/                          # Shared service tests
│   │   └── __init__.py
│   └── requirements.txt
│
├── frontend/                           # React + Vite + TypeScript
│   ├── src/
│   │   ├── features/                   # Feature modules
│   │   │   └── bond-spreads/           # First feature
│   │   │       └── (components, hooks, types — built in step 3)
│   │   ├── shared/                     # Shared UI components, theme, layout
│   │   │   └── (built in step 3)
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── index.html
│   ├── vite.config.ts
│   ├── tsconfig.json
│   └── package.json
│
├── .github/
│   └── workflows/                      # empty for now
│
├── .gitignore
└── README.md
```

## CDK Stacks — Full Specification

Stage is passed as CDK context: `cdk deploy -c stage=box`

**Naming**: all resources include `{stage}` — e.g., `fm-box-table` (prefix `fm` for Financial Monitor)
**Tags** on all resources: `Project: FinancialMonitor`, `Stage: {stage}`, `ManagedBy: CDK`
**AWS account**: use `process.env.CDK_DEFAULT_ACCOUNT` (placeholder)
**Region**: `eu-central-1`

### Core Stacks (shared by all features)

#### `core/config-stack.ts` — SSM Parameters
- `/fm/{stage}/alert-email` — String, default: `grzegorz.karolak@outlook.com`
- `/fm/{stage}/cost-limit-warning` — String, default: `10`
- `/fm/{stage}/cost-limit-critical` — String, default: `15`
- `/fm/{stage}/kill-switch` — String, default: `false`
- `/fm/{stage}/features/bond-spreads/fred-api-key` — SecureString, dummy initial value

#### `core/storage-stack.ts` — DynamoDB + S3
**DynamoDB table**: `fm-{stage}-data` (single table for all features)
- Partition key: `PK` (String)
- Sort key: `SK` (String)
- GSI1: `GSI1PK` (String) + `GSI1SK` (Number), projection ALL
- Pay-per-request billing
- Point-in-time recovery enabled

**S3 bucket**: `fm-{stage}-frontend-{accountId}` (globally unique)
- Block all public access
- Versioning disabled
- Auto-delete objects on stack destroy (for sandbox)
- RemovalPolicy.DESTROY for sandbox, RETAIN for production

#### `core/cdn-stack.ts` — CloudFront
- S3 origin with OAC (Origin Access Control)
- Default behavior: S3 origin, redirect HTTP→HTTPS
- Cache behaviors:
  - `/data/*` — TTL 30 days (2,592,000s), cache by path only (covers all feature data)
  - `/assets/*` — TTL 1 year (31,536,000s), Vite hashed files
  - `/index.html` — TTL 0 (no-cache, always fresh)
- Custom error responses: 403→/index.html (200), 404→/index.html (200)
- Price class: PriceClass_100 (US, Canada, Europe)
- Output the distribution domain name and ID

#### `core/monitoring-stack.ts` — Alerts, Budget, Kill Switch
**SNS Topic**: `fm-{stage}-alerts`
- Email subscription from SSM `alert-email`

**CloudWatch Alarms** (generic, per-Lambda — each feature stack passes its Lambda references):
- Lambda errors > 0 in 1 evaluation → SNS
- Lambda duration > 80% of timeout → SNS

**AWS Budget**:
- $10 → SNS warning
- $15 → SNS critical + kill switch Lambda
- **Kill Switch Lambda**: sets SSM `kill-switch` to `true`, disables all EventBridge rules, publishes SNS alert

### Feature Stacks

#### `features/bond-spreads-stack.ts` — Bond Spreads Feature
Receives shared resources (table, bucket, distribution, SNS topic) as props from core stacks.

**Ingest Lambda**: `fm-{stage}-bond-spreads-ingest`
- Runtime: Python 3.12, Memory: 512MB, Timeout: 5min
- Reserved concurrency: 1
- Code: `../backend` directory
- Handler: `features/bond_spreads/handlers/ingest.handler`
- Environment: `STAGE`, `TABLE_NAME`, `BUCKET_NAME`, `DISTRIBUTION_ID`, `SSM_PREFIX=/fm/{stage}`, `FEATURE=bond-spreads`, `DATA_PREFIX=data/bond-spreads`
- Permissions: DynamoDB read/write, S3 put, CloudFront invalidation, SSM read

**Backfill Lambda**: `fm-{stage}-bond-spreads-backfill`
- Same but: Memory 1024MB, Timeout 15min
- Handler: `features/bond_spreads/handlers/backfill.handler`

**EventBridge rule**: `fm-{stage}-bond-spreads-monthly`
- Schedule: `cron(0 8 1 * ? *)` → triggers ingest Lambda

**CDK Custom Resource**: triggers backfill Lambda on first deploy
- Backfill checks if data exists and skips if populated

**Register alarms**: pass Lambda references to monitoring stack for alarm creation

## DynamoDB Key Design (multi-feature ready)

All bond spread records use the `BS#` prefix to namespace within the shared table:

| PK (String) | SK (String) | GSI1PK (String) | GSI1SK (Number) |
|---|---|---|---|
| `BS#COUNTRY#US` | `2025-01` | `BS#PERIOD#2025-01` | 186 (spread_bps) |
| `BS#COUNTRY#US` | `2025-02` | `BS#PERIOD#2025-02` | 192 |
| `BS#COUNTRY#DE` | `2025-01` | `BS#PERIOD#2025-01` | -12 |
| `BS#META` | `LAST_INGEST` | — | — |

Future features use their own prefix (e.g., `FX#`, `EQ#`, `CMD#`).

## S3 Data Path (multi-feature ready)

Bond spread JSON files go under `/data/bond-spreads/`:
```
s3://bucket/data/bond-spreads/spreads-latest.json
s3://bucket/data/bond-spreads/spreads-history.json
s3://bucket/data/bond-spreads/spreads-summary.json
```

Future features: `/data/currency-rates/*.json`, `/data/equity-indices/*.json`, etc.

## Output

After running this step:
1. `cd infra && npm install && npx cdk synth -c stage=box` — no errors
2. `npx cdk deploy --all -c stage=box` — all stacks created
3. Shared resources: DynamoDB table, S3 bucket, CloudFront, SNS, budgets
4. Feature resources: 2 Lambdas, EventBridge rule, CloudWatch alarms
5. Placeholder Lambda functions deployed

## Important
- Use `aws-cdk-lib` v2 (not v1)
- Do NOT install `@aws-cdk/` scoped packages
- Feature stacks receive shared resources as constructor props — loose coupling
- Adding a new feature = new feature stack + new backend feature module, no changes to core stacks
