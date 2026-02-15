# Step 5: Integration Verification, Documentation & README

## Context
This is the final step of **Financial Monitor**.
- Step 0: CDK infrastructure (core + bond-spreads feature)
- Step 1: Backend shared + bond-spreads services
- Step 2: Lambda handlers
- Step 3: React frontend (shared shell + bond-spreads feature)
- Step 4: CI/CD pipelines

## Task

1. Review entire project for consistency
2. Create **README.md** (quick start)
3. Create **full technical documentation** in `/docs`
4. Create local dev scripts
5. Verify everything compiles and tests pass

---

## Documentation Structure

```
financial-monitor/
├── README.md                               Quick start, overview, links to /docs
├── docs/
│   ├── architecture.md                     System architecture & design decisions
│   ├── data-flow.md                        End-to-end data pipeline explanation
│   ├── dynamodb-schema.md                  Table design, key patterns, GSI, examples
│   ├── s3-data-contracts.md                JSON file schemas (API contract for frontend)
│   ├── infrastructure.md                   AWS resources, CDK stacks, cost model
│   ├── deployment.md                       Step-by-step deployment guide (BOX + PRO)
│   ├── ci-cd.md                            GitHub Actions pipeline documentation
│   ├── monitoring.md                       Alerts, budgets, kill switch, troubleshooting
│   ├── frontend.md                         Component architecture, theming, responsive design
│   ├── adding-a-feature.md                 Guide: how to add a new feature module
│   └── fred-api.md                         FRED API integration details, series IDs, rate limits
```

---

## `/docs/architecture.md` — System Architecture

Must include:

**High-level diagram** (ASCII art that can render in GitHub):
```
User → CloudFront → S3 (React SPA + /data/{feature}/*.json)
                          ▲
                          │ writes
FRED API → Lambda → DynamoDB (source of truth)
                  → S3 /data/ (pre-computed view)
                  → CloudFront invalidation
```

**Sections:**
- Architecture overview + CQRS-lite pattern explanation
- Why no API Gateway (cost, security, simplicity)
- Why pre-computed JSON on S3 vs dynamic API
- Why single DynamoDB table (single-table design with feature prefixes)
- Why CloudFront + S3 (cost model, caching strategy, attack resilience)
- Technology choices and rationale:
  - React + Vite (not Next.js) — why
  - Python Lambdas (not Node.js) — why
  - CDK (not SAM, not Terraform) — why
  - React Query (not Redux) — why
  - Plain CSS (not Tailwind, not styled-components) — why
- Modular feature architecture explanation with diagram:
  ```
  ┌─────────────────────────────────────┐
  │           CORE (shared)             │
  │  DynamoDB │ S3 │ CloudFront │ SNS   │
  └─────────┬───────────┬──────────────┘
            │           │
  ┌─────────▼──┐  ┌─────▼──────────┐
  │ Bond       │  │ Currency Rates  │  ← future
  │ Spreads    │  │ (example)       │
  │ BS# prefix │  │ FX# prefix     │
  └────────────┘  └────────────────┘
  ```
- Extensibility: how new features plug in without touching existing code

## `/docs/data-flow.md` — Data Pipeline

Must include:

**Monthly ingestion flow** (step-by-step with numbered diagram):
1. EventBridge triggers ingest Lambda (1st of month, 08:00 UTC)
2. Lambda checks kill switch in SSM → abort if active
3. Lambda reads FRED API key from SSM
4. For each country in config:
   - Fetch 10Y yield from FRED
   - Fetch 3M rate from FRED
   - Calculate spread (pure function)
   - Write to DynamoDB with `BS#COUNTRY#{code}` key
5. Generate 3 JSON files from DynamoDB data
6. Upload to S3 under `data/bond-spreads/`
7. Invalidate CloudFront `/data/bond-spreads/*`
8. Update `BS#META` / `LAST_INGEST` record

**Backfill flow** (similar, with differences highlighted):
- Triggered by CDK Custom Resource (first deploy only)
- Fetches 10 years of history per country
- Batch writes to DynamoDB
- Idempotent: checks if `BS#` data exists first

**Frontend data flow**:
1. React app loads from CloudFront
2. React Query hooks fetch `/data/bond-spreads/*.json` (static files, cached 30 days)
3. All sorting, filtering, searching happens client-side (dataset is ~100KB)
4. No backend calls during user interaction

**Data freshness timeline**:
```
FRED publishes data ──→ ~1 month lag ──→ Lambda fetches ──→ S3 JSON updated
                                         (1st of month)     (CloudFront cache invalidated)
                                                            ──→ Users see new data
```

## `/docs/dynamodb-schema.md` — DynamoDB Table Design

Must include:

**Table specification**:
- Table name: `fm-{stage}-data`
- Billing: pay-per-request (on-demand)
- Point-in-time recovery: enabled

**Key schema**:
| Key | Type | Description |
|-----|------|-------------|
| PK | String | Partition key — format: `{FEATURE_PREFIX}#{ENTITY}#{ID}` |
| SK | String | Sort key — format varies by entity |
| GSI1PK | String | Global Secondary Index partition key |
| GSI1SK | Number | Global Secondary Index sort key |

**Bond Spreads records** (prefix `BS#`):

| PK | SK | GSI1PK | GSI1SK | Example Attributes |
|----|-----|--------|--------|-------------------|
| `BS#COUNTRY#US` | `2025-01` | `BS#PERIOD#2025-01` | `186` | country_name, currency, flag, yield_10y, yield_3m, spread, spread_bps, updated_at |
| `BS#COUNTRY#US` | `2025-02` | `BS#PERIOD#2025-02` | `192` | ... |
| `BS#COUNTRY#DE` | `2025-01` | `BS#PERIOD#2025-01` | `-12` | ... |
| `BS#META` | `LAST_INGEST` | — | — | last_ingest_date, countries_count, errors |

**Access patterns**:
| Pattern | Query | Used By |
|---------|-------|---------|
| Get all months for a country | PK = `BS#COUNTRY#US`, SK between | `json_generator` (history) |
| Get all countries for a month | GSI1PK = `BS#PERIOD#2025-01` | `json_generator` (latest, summary) |
| Get all countries sorted by spread | GSI1PK = `BS#PERIOD#2025-01`, sort by GSI1SK | `json_generator` (ranking) |
| Check if data exists | Scan with PK begins_with `BS#`, limit 1 | `backfill` (idempotency) |
| Check specific record | PK = `BS#COUNTRY#US`, SK = `2025-01` | `ingest` (skip existing) |

**Future feature namespacing**:
```
FX#PAIR#USDEUR     │ 2025-01    → Currency rates feature
EQ#INDEX#SP500      │ 2025-01    → Equity indices feature
CMD#COMMODITY#GOLD  │ 2025-01    → Commodities feature
```

**Sample DynamoDB item** (full JSON):
```json
{
  "PK": "BS#COUNTRY#US",
  "SK": "2025-01",
  "GSI1PK": "BS#PERIOD#2025-01",
  "GSI1SK": 186,
  "country_code": "US",
  "country_name": "United States",
  "currency": "USD",
  "flag": "🇺🇸",
  "yield_10y": 4.52,
  "yield_3m": 2.66,
  "spread": 1.86,
  "spread_bps": 186,
  "updated_at": "2025-02-01T08:15:00Z"
}
```

## `/docs/s3-data-contracts.md` — JSON File Schemas

Document the exact JSON schema for each file. These are the **API contract** between backend and frontend.

**Files:**
- `/data/bond-spreads/spreads-latest.json` — full schema with all fields, types, example
- `/data/bond-spreads/spreads-history.json` — full schema with all fields, types, example
- `/data/bond-spreads/spreads-summary.json` — full schema with all fields, types, example

**For each file, include:**
- File path on S3
- CloudFront cache behavior (TTL, invalidation trigger)
- Complete JSON schema with field descriptions and types
- Full example JSON
- File size estimate
- When it's generated (monthly by ingest Lambda)
- Which frontend hooks consume it

**Also document the convention** for future features:
```
/data/{feature-name}/{file-name}.json
```

## `/docs/infrastructure.md` — AWS Resources

Must include:

**Resource inventory** — table of all AWS resources with:
| Resource | Name Pattern | Stack | Purpose |
|----------|-------------|-------|---------|
| DynamoDB | `fm-{stage}-data` | StorageStack | Source of truth |
| S3 | `fm-{stage}-frontend-{account}` | StorageStack | Static hosting + data |
| CloudFront | — | CdnStack | CDN + caching |
| Lambda | `fm-{stage}-bond-spreads-ingest` | BondSpreadsStack | Monthly data fetch |
| Lambda | `fm-{stage}-bond-spreads-backfill` | BondSpreadsStack | Historical load |
| EventBridge | `fm-{stage}-bond-spreads-monthly` | BondSpreadsStack | Monthly trigger |
| SNS | `fm-{stage}-alerts` | MonitoringStack | Alert notifications |
| Budget | — | MonitoringStack | Cost protection |
| Lambda | `fm-{stage}-kill-switch` | MonitoringStack | Auto cost cutoff |
| SSM | `/fm/{stage}/*` | ConfigStack | Configuration |

**CDK stack dependency graph**:
```
ConfigStack
    ↓
StorageStack (DynamoDB, S3)
    ↓
CdnStack (CloudFront → S3)
    ↓
MonitoringStack (SNS, Budgets, Alarms)
    ↓
BondSpreadsStack (Lambdas, EventBridge → uses all above)
```

**SSM Parameter inventory**:
| Path | Type | Default | Description |
|------|------|---------|-------------|
| `/fm/{stage}/alert-email` | String | grzegorz.karolak@outlook.com | Alert recipient |
| `/fm/{stage}/cost-limit-warning` | String | 10 | Budget warning ($) |
| `/fm/{stage}/cost-limit-critical` | String | 15 | Budget critical ($) |
| `/fm/{stage}/kill-switch` | String | false | Emergency stop |
| `/fm/{stage}/features/bond-spreads/fred-api-key` | SecureString | — | FRED API key |

**CloudFront cache policy**:
| Path Pattern | TTL | Invalidation Trigger |
|--------------|-----|---------------------|
| `/index.html` | 0 (no-cache) | Frontend deploy |
| `/assets/*` | 1 year | Never (content-hashed) |
| `/data/*` | 30 days | Lambda data ingestion |

**Cost model** — monthly estimates table + cost protection layers (6 layers explained)

**IAM permissions matrix** — which Lambda has access to what

## `/docs/deployment.md` — Deployment Guide

Step-by-step instructions:

**Prerequisites** — what you need installed, AWS account setup

**First-time deployment (BOX)**:
1. Clone repo, install dependencies
2. CDK bootstrap (if first time in account)
3. `cdk deploy --all -c stage=box`
4. Set FRED API key in SSM (exact command)
5. Confirm SNS email subscription
6. Build and deploy frontend (exact commands)
7. Verify: open CloudFront URL, check data loaded
8. Check CloudWatch logs for backfill Lambda

**Subsequent deployments**: just push to main (CI/CD handles it)

**Production deployment (PRO)**:
1. Set up separate AWS credentials
2. Configure GitHub secrets
3. Manual trigger in GitHub Actions
4. Verification steps

**Manual operations**:
- How to trigger backfill manually
- How to trigger ingest manually
- How to check kill switch status
- How to reset kill switch
- How to check Lambda logs
- How to invalidate CloudFront cache manually

**Rollback procedures**:
- Frontend: redeploy previous git commit
- Backend: CDK deploy previous commit (Lambdas update automatically)
- Data: DynamoDB has point-in-time recovery

## `/docs/ci-cd.md` — CI/CD Pipeline

**Pipeline diagrams** for both workflows (BOX and PRO):
```
Push to main
  → Run Python tests (shared + bond-spreads)
  → Run frontend tests (vitest)
  → CDK deploy all stacks
  → Extract CDK outputs (bucket name, distribution ID)
  → Build frontend (vite build)
  → Sync to S3 (with correct cache headers)
  → Invalidate CloudFront
```

**Environment separation**: BOX vs PRO (different credentials, different stacks, same code)

**GitHub secrets reference**

**Troubleshooting common CI/CD failures**:
- CDK deploy fails: check CloudFormation console
- S3 sync fails: check bucket permissions
- Tests fail: run locally first
- CDK outputs extraction fails: check output key names

## `/docs/monitoring.md` — Monitoring & Alerting

**What's monitored**:
- Lambda execution errors → SNS email
- Lambda duration approaching timeout → SNS email
- Monthly AWS spend → Budget alerts at $10 and $15

**Kill switch mechanism** (detailed flow):
```
AWS Budget $15 exceeded
  → SNS notification
  → Kill Switch Lambda triggered
  → Sets SSM /fm/{stage}/kill-switch = "true"
  → Disables EventBridge rule
  → Sends detailed SNS alert
  → All future Lambda invocations check flag and abort
```

**How to investigate issues**:
- Where to find Lambda logs (CloudWatch log groups)
- How to read structured JSON logs
- Common error patterns and solutions:
  - FRED API key invalid
  - FRED rate limit hit
  - Country series ID doesn't exist
  - DynamoDB throttling (unlikely with pay-per-request)
  - S3 permissions error

**How to reset after kill switch**:
```bash
# 1. Check current status
aws ssm get-parameter --name "/fm/box/kill-switch"

# 2. Reset kill switch
aws ssm put-parameter --name "/fm/box/kill-switch" --value "false" --overwrite

# 3. Re-enable EventBridge rule
aws events enable-rule --name "fm-box-bond-spreads-monthly"

# 4. Verify
aws events describe-rule --name "fm-box-bond-spreads-monthly"
```

## `/docs/frontend.md` — Frontend Architecture

**Component hierarchy** (tree diagram)

**Feature module pattern**:
- How shared vs feature code is organized
- Import rules: features never import from other features
- Shared components available to all features

**Theming system**:
- CSS variable structure
- How dark/light toggle works
- How to add new theme variables

**Responsive breakpoints**:
| Breakpoint | Layout Changes |
|-----------|---------------|
| >1024px (desktop) | Full table, 2-column bottom grid |
| ≤1024px (tablet) | 2-col stats, single-column bottom |
| ≤768px (mobile) | Card layout, horizontal scroll tags |
| ≤420px (small) | Compact padding, hidden currency codes |

**Data fetching strategy**:
- React Query configuration (staleTime, gcTime, retry)
- Cache behavior: fetches once, serves from memory
- Loading/error state handling

**State management**:
- ThemeContext (shared): dark/light, localStorage
- BondSpreadsUIContext (feature): sort, filter, time period

## `/docs/adding-a-feature.md` — How to Add a New Feature

Step-by-step guide with example ("Adding Currency Rates"):

**1. Backend** — create `backend/features/currency_rates/`:
```
currency_rates/
├── handlers/
│   ├── ingest.py
│   └── backfill.py
├── services/
│   ├── config.py
│   ├── api_client.py
│   ├── rate_calculator.py
│   └── json_generator.py
├── models/
│   └── types.py
└── tests/
```

**2. DynamoDB** — choose a prefix:
- Use `FX#` prefix (e.g., `FX#PAIR#USDEUR`, `FX#META`)
- Same shared table, no schema changes needed

**3. S3** — data goes to `/data/currency-rates/`:
- `data/currency-rates/rates-latest.json`
- `data/currency-rates/rates-history.json`

**4. Infrastructure** — create `infra/lib/stacks/features/currency-rates-stack.ts`:
- New Lambdas, new EventBridge rule
- Receives shared resources (table, bucket, distribution) as props
- Register with monitoring stack for alarms

**5. Frontend** — create `frontend/src/features/currency-rates/`:
- Own components, hooks, context, types, styles
- Add route/navigation in App.tsx

**Checklist**: what you need, what you DON'T need to change, common pitfalls

## `/docs/fred-api.md` — FRED API Integration

**API details**:
- Base URL, authentication, rate limits (120 req/min)
- How to get an API key
- Data frequency and lag (~1 month delay)

**Series ID reference table** — all tracked countries with:
| Country | Flag | 10Y Series | 3M Series | Verified | Notes |
|---------|------|-----------|----------|----------|-------|
| US | 🇺🇸 | GS10 | TB3MS | ✅ | Direct treasury yields |
| UK | 🇬🇧 | IRLTLT01GBM156N | IR3TIB01GBM156N | ✅/❓ | OECD pattern |
| ... | | | | | |

**How to add a new country**: find series IDs on FRED, add to config.py

**How to verify a series ID**: curl example + expected response

**Common FRED API issues**: missing data ("."), series discontinued, frequency mismatches

---

## README.md (Quick Start)

Keep the README concise — it's the entry point, not the full docs. Structure:

```markdown
# Financial Monitor

Modular financial data platform for tracking economic indicators.

## Features

### 📊 Bond Spreads Dashboard
Track government bond yield curve spreads (10Y-3M) for 12 major economies.
Monitor inversions, compare trends, spot recession signals.

*More features planned...*

## Quick Start

[5-step deploy guide — install, deploy, set API key, build frontend, access]

## Development

[How to run tests, start dev server, CDK commands]

## Documentation

Full technical documentation in [`/docs`](./docs/):

| Document | Description |
|----------|-------------|
| [Architecture](docs/architecture.md) | System design, patterns, decisions |
| [Data Flow](docs/data-flow.md) | End-to-end data pipeline |
| [DynamoDB Schema](docs/dynamodb-schema.md) | Table design, keys, access patterns |
| [S3 Data Contracts](docs/s3-data-contracts.md) | JSON schemas (backend↔frontend API) |
| [Infrastructure](docs/infrastructure.md) | AWS resources, CDK stacks, costs |
| [Deployment](docs/deployment.md) | Step-by-step deploy guide |
| [CI/CD](docs/ci-cd.md) | GitHub Actions pipelines |
| [Monitoring](docs/monitoring.md) | Alerts, kill switch, troubleshooting |
| [Frontend](docs/frontend.md) | Components, theming, responsive |
| [Adding a Feature](docs/adding-a-feature.md) | How to extend the platform |
| [FRED API](docs/fred-api.md) | Data source integration |

## Cost

< $1/month normal operation. Budget alerts at $10/$15 with automatic kill switch.

## License

[Choose license]
```

---

## Helper Scripts

### `scripts/create-mock-data.py`
Generates mock JSON in `frontend/public/data/bond-spreads/` for local dev.

### `scripts/trigger-backfill.sh`
```bash
#!/bin/bash
STAGE=${1:-box}
echo "Triggering bond-spreads backfill (${STAGE})"
aws lambda invoke --function-name fm-${STAGE}-bond-spreads-backfill \
  --payload '{}' --region eu-central-1 /tmp/backfill-response.json
cat /tmp/backfill-response.json
```

### `scripts/trigger-ingest.sh`
```bash
#!/bin/bash
STAGE=${1:-box}
echo "Triggering bond-spreads ingest (${STAGE})"
aws lambda invoke --function-name fm-${STAGE}-bond-spreads-ingest \
  --payload '{}' --region eu-central-1 /tmp/ingest-response.json
cat /tmp/ingest-response.json
```

---

## Verification Checklist

### Infrastructure
- [ ] `cd infra && npm install && npx cdk synth -c stage=box` — no errors
- [ ] Core stacks pass shared resources to feature stacks
- [ ] Lambda handlers point to `features/bond_spreads/handlers/ingest.handler`
- [ ] Environment variables match handler expectations
- [ ] Resource naming: `fm-{stage}-*`
- [ ] SSM paths: `/fm/{stage}/...`

### Backend
- [ ] `cd backend && python -m pytest tests/ features/bond_spreads/tests/ -v` — all pass
- [ ] Shared services: no feature-specific imports
- [ ] Bond spreads: uses `BS#` prefix, `data/bond-spreads/` path
- [ ] JSON output matches frontend TypeScript interfaces

### Frontend
- [ ] `cd frontend && npm install && npm run build` — succeeds
- [ ] `cd frontend && npx vitest run` — all pass
- [ ] Shared components: no feature imports
- [ ] Bond spreads: self-contained under `features/bond-spreads/`
- [ ] Data hooks fetch from `/data/bond-spreads/*.json`
- [ ] Responsive at all breakpoints
- [ ] Theme toggle works

### Documentation
- [ ] README.md links to all /docs files
- [ ] All 11 /docs files are complete with diagrams, tables, examples
- [ ] DynamoDB schema doc has sample items
- [ ] S3 data contracts have full JSON examples
- [ ] Deployment guide has exact CLI commands
- [ ] Adding-a-feature guide is actionable (someone could follow it)
- [ ] FRED API doc has verified series IDs table

### CI/CD
- [ ] Both workflows valid YAML, correct triggers
- [ ] Test paths include shared + feature tests
- [ ] `.gitignore` covers all generated files

## Final State

After this step:
1. All code compiles and tests pass ✅
2. README links to comprehensive /docs ✅
3. 11 documentation files covering every aspect of the system ✅
4. Adding a new feature is documented step-by-step ✅
5. Ready for `git init && git add . && git commit`
