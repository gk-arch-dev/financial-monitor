#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { ConfigStack } from '../lib/stacks/core/config-stack';
import { StorageCdnStack } from '../lib/stacks/core/storage-cdn-stack';
import { MonitoringStack } from '../lib/stacks/core/monitoring-stack';
import { BondSpreadsStack } from '../lib/stacks/features/bond-spreads-stack';

const app = new cdk.App();

// Get stage from CDK context: cdk deploy -c stage=box
const stage = app.node.tryGetContext('stage');
if (!stage) {
  throw new Error('Stage is required. Use: cdk deploy -c stage=box');
}

if (!['box', 'pro'].includes(stage)) {
  throw new Error('Stage must be "box" (sandbox) or "pro" (production)');
}

// Capitalize first letter for stack names
const stageCapitalized = stage.charAt(0).toUpperCase() + stage.slice(1);

// Common environment configuration
const env = {
  account: process.env.CDK_DEFAULT_ACCOUNT,
  region: 'eu-central-1',
};

// Apply default tags to all resources
cdk.Tags.of(app).add('Project', 'FinancialMonitor');
cdk.Tags.of(app).add('Stage', stage);
cdk.Tags.of(app).add('ManagedBy', 'CDK');

// ================================================config-stack.ts=============================
// Core Stacks
// =============================================================================

// Config Stack - SSM Parameters
const configStack = new ConfigStack(app, `FmCoreConfig${stageCapitalized}`, {
  stage,
  env,
  description: 'Financial Monitor - SSM configuration parameters',
});

// Storage + CDN Stack - DynamoDB, S3, CloudFront
// Note: Combined into single stack to avoid cross-stack cyclic dependencies
// with CloudFront Origin Access Control and S3 bucket policies
const storageCdnStack = new StorageCdnStack(app, `FmCoreStorageCdn${stageCapitalized}`, {
  stage,
  env,
  description: 'Financial Monitor - DynamoDB, S3, and CloudFront',
});

// Monitoring Stack - SNS, Budgets, Alarms
const monitoringStack = new MonitoringStack(app, `FmCoreMonitoring${stageCapitalized}`, {
  stage,
  alertEmail: configStack.alertEmail,
  ssmPrefix: configStack.ssmPrefix,
  env,
  description: 'Financial Monitor - Monitoring, alerts, and budgets',
});

// =============================================================================
// Feature Stacks
// =============================================================================

// Bond Spreads Feature
const bondSpreadsStack = new BondSpreadsStack(app, `FmFeatureBondSpreads${stageCapitalized}`, {
  stage,
  table: storageCdnStack.table,
  bucket: storageCdnStack.bucket,
  distribution: storageCdnStack.distribution,
  alertTopic: monitoringStack.alertTopic,
  ssmPrefix: configStack.ssmPrefix,
  env,
  description: 'Financial Monitor - Bond Spreads feature',
});

// =============================================================================
// Stack Dependencies
// =============================================================================

monitoringStack.addDependency(configStack);
bondSpreadsStack.addDependency(storageCdnStack);
bondSpreadsStack.addDependency(monitoringStack);

// Note: CloudWatch alarms for Lambdas are created within the BondSpreadsStack
// to avoid cross-stack cyclic dependencies
