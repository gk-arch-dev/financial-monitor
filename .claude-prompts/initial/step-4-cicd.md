# Step 4: CI/CD — GitHub Actions Pipelines

## Context
This is step 4 of **Financial Monitor**.
- Step 0: CDK infrastructure (core stacks + bond-spreads feature stack)
- Step 1: Backend shared services + bond-spreads feature services
- Step 2: Lambda handlers
- Step 3: React frontend (shared shell + bond-spreads feature)

We now create GitHub Actions workflows.

## Task

Create two workflow files for BOX (automatic) and PRO (manual) deployments.

## `.github/workflows/deploy-box.yml` — Sandbox (automatic)

**Trigger**: push to `main` branch

```yaml
name: Deploy to BOX

on:
  push:
    branches: [main]

env:
  AWS_REGION: eu-central-1
  STAGE: box

jobs:
  test:
    name: Run Tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Install Python dependencies
        run: cd backend && pip install -r requirements.txt
      - name: Run Python tests
        run: |
          cd backend
          python -m pytest tests/ features/bond_spreads/tests/ -v --tb=short

      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json
      - name: Install frontend dependencies
        run: cd frontend && npm ci
      - name: Run frontend tests
        run: cd frontend && npx vitest run

  deploy:
    name: Deploy to BOX
    needs: test
    runs-on: ubuntu-latest
    permissions:
      contents: read
      id-token: write
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: infra/package-lock.json
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID_BOX }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY_BOX }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Install CDK dependencies
        run: cd infra && npm ci
      - name: Install backend dependencies
        run: cd backend && pip install -r requirements.txt -t .package
      - name: CDK Deploy
        run: |
          cd infra
          npx cdk deploy --all -c stage=${{ env.STAGE }} --require-approval never --outputs-file cdk-outputs.json

      - name: Extract CDK outputs
        id: cdk-outputs
        run: |
          BUCKET=$(cat infra/cdk-outputs.json | python3 -c "import sys,json; d=json.load(sys.stdin); print([v for k,v in [(k2,v2) for s in d.values() for k2,v2 in s.items()] if 'BucketName' in k][0])")
          DIST_ID=$(cat infra/cdk-outputs.json | python3 -c "import sys,json; d=json.load(sys.stdin); print([v for k,v in [(k2,v2) for s in d.values() for k2,v2 in s.items()] if 'DistributionId' in k][0])")
          echo "bucket=$BUCKET" >> $GITHUB_OUTPUT
          echo "distribution_id=$DIST_ID" >> $GITHUB_OUTPUT

      - name: Install frontend dependencies
        run: cd frontend && npm ci
      - name: Build frontend
        run: cd frontend && npm run build
      - name: Sync frontend to S3
        run: |
          aws s3 sync frontend/dist/ s3://${{ steps.cdk-outputs.outputs.bucket }}/ \
            --delete \
            --cache-control "public, max-age=31536000" \
            --exclude "index.html" \
            --exclude "data/*"
          aws s3 cp frontend/dist/index.html s3://${{ steps.cdk-outputs.outputs.bucket }}/index.html \
            --cache-control "no-cache, no-store, must-revalidate"
          aws s3 cp frontend/dist/robots.txt s3://${{ steps.cdk-outputs.outputs.bucket }}/robots.txt --cache-control "public, max-age=86400" 2>/dev/null || true
          aws s3 cp frontend/dist/sitemap.xml s3://${{ steps.cdk-outputs.outputs.bucket }}/sitemap.xml --cache-control "public, max-age=86400" 2>/dev/null || true

      - name: Invalidate CloudFront cache
        run: |
          aws cloudfront create-invalidation \
            --distribution-id ${{ steps.cdk-outputs.outputs.distribution_id }} \
            --paths "/*"

      - name: Deployment summary
        run: |
          echo "## BOX Deployment Complete ✅" >> $GITHUB_STEP_SUMMARY
          echo "- S3 Bucket: ${{ steps.cdk-outputs.outputs.bucket }}" >> $GITHUB_STEP_SUMMARY
          echo "- CloudFront: ${{ steps.cdk-outputs.outputs.distribution_id }}" >> $GITHUB_STEP_SUMMARY
```

## `.github/workflows/deploy-pro.yml` — Production (manual)

**Trigger**: `workflow_dispatch` with confirmation

```yaml
name: Deploy to PRO

on:
  workflow_dispatch:
    inputs:
      confirm:
        description: 'Type "deploy-pro" to confirm production deployment'
        required: true
        type: string

env:
  AWS_REGION: eu-central-1
  STAGE: pro

jobs:
  validate:
    name: Validate Confirmation
    runs-on: ubuntu-latest
    steps:
      - name: Check confirmation
        if: github.event.inputs.confirm != 'deploy-pro'
        run: |
          echo "❌ Confirmation failed. Type 'deploy-pro' to confirm."
          exit 1

  test:
    name: Run Tests
    needs: validate
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Install Python dependencies
        run: cd backend && pip install -r requirements.txt
      - name: Run Python tests
        run: cd backend && python -m pytest tests/ features/bond_spreads/tests/ -v --tb=short
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json
      - name: Install frontend dependencies
        run: cd frontend && npm ci
      - name: Run frontend tests
        run: cd frontend && npx vitest run

  deploy:
    name: Deploy to PRO
    needs: test
    runs-on: ubuntu-latest
    permissions:
      contents: read
      id-token: write
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: infra/package-lock.json
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID_PRO }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY_PRO }}
          aws-region: ${{ env.AWS_REGION }}
      - name: Install CDK dependencies
        run: cd infra && npm ci
      - name: Install backend dependencies
        run: cd backend && pip install -r requirements.txt -t .package
      - name: CDK Deploy
        run: cd infra && npx cdk deploy --all -c stage=${{ env.STAGE }} --require-approval never --outputs-file cdk-outputs.json
      - name: Extract CDK outputs
        id: cdk-outputs
        run: |
          BUCKET=$(cat infra/cdk-outputs.json | python3 -c "import sys,json; d=json.load(sys.stdin); print([v for k,v in [(k2,v2) for s in d.values() for k2,v2 in s.items()] if 'BucketName' in k][0])")
          DIST_ID=$(cat infra/cdk-outputs.json | python3 -c "import sys,json; d=json.load(sys.stdin); print([v for k,v in [(k2,v2) for s in d.values() for k2,v2 in s.items()] if 'DistributionId' in k][0])")
          echo "bucket=$BUCKET" >> $GITHUB_OUTPUT
          echo "distribution_id=$DIST_ID" >> $GITHUB_OUTPUT
      - name: Install frontend dependencies
        run: cd frontend && npm ci
      - name: Build frontend
        run: cd frontend && npm run build
      - name: Sync frontend to S3
        run: |
          aws s3 sync frontend/dist/ s3://${{ steps.cdk-outputs.outputs.bucket }}/ \
            --delete \
            --cache-control "public, max-age=31536000" \
            --exclude "index.html" \
            --exclude "data/*"
          aws s3 cp frontend/dist/index.html s3://${{ steps.cdk-outputs.outputs.bucket }}/index.html \
            --cache-control "no-cache, no-store, must-revalidate"
          aws s3 cp frontend/dist/robots.txt s3://${{ steps.cdk-outputs.outputs.bucket }}/robots.txt --cache-control "public, max-age=86400" 2>/dev/null || true
          aws s3 cp frontend/dist/sitemap.xml s3://${{ steps.cdk-outputs.outputs.bucket }}/sitemap.xml --cache-control "public, max-age=86400" 2>/dev/null || true
      - name: Invalidate CloudFront cache
        run: |
          aws cloudfront create-invalidation \
            --distribution-id ${{ steps.cdk-outputs.outputs.distribution_id }} \
            --paths "/*"
      - name: Deployment summary
        run: |
          echo "## PRO Deployment Complete 🚀" >> $GITHUB_STEP_SUMMARY
          echo "- S3 Bucket: ${{ steps.cdk-outputs.outputs.bucket }}" >> $GITHUB_STEP_SUMMARY
          echo "- CloudFront: ${{ steps.cdk-outputs.outputs.distribution_id }}" >> $GITHUB_STEP_SUMMARY
```

## GitHub Secrets Required

| Secret | Description |
|--------|-------------|
| `AWS_ACCESS_KEY_ID_BOX` | IAM access key for sandbox |
| `AWS_SECRET_ACCESS_KEY_BOX` | IAM secret key for sandbox |
| `AWS_ACCESS_KEY_ID_PRO` | IAM access key for production |
| `AWS_SECRET_ACCESS_KEY_PRO` | IAM secret key for production |

## Key Details

- **Python test paths**: `tests/` (shared) + `features/bond_spreads/tests/` (feature)
- **S3 sync excludes `data/*`**: protects all feature data directories (`data/bond-spreads/`, future `data/currency-rates/`, etc.)
- **Full CloudFront invalidation on deploy**: `/*` clears all cached content
- **PRO safety**: requires typing "deploy-pro" as confirmation

## `.gitignore`

```
node_modules/
backend/.package/
__pycache__/
*.pyc
frontend/dist/
*.js.map
infra/cdk.out/
infra/cdk-outputs.json
.idea/
.vscode/
*.swp
.DS_Store
Thumbs.db
.env
.env.local
coverage/
.pytest_cache/
```
