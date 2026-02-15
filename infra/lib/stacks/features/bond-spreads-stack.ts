import * as cdk from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as cloudfront from 'aws-cdk-lib/aws-cloudfront';
import * as sns from 'aws-cdk-lib/aws-sns';
import * as events from 'aws-cdk-lib/aws-events';
import * as targets from 'aws-cdk-lib/aws-events-targets';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as cr from 'aws-cdk-lib/custom-resources';
import * as cloudwatch from 'aws-cdk-lib/aws-cloudwatch';
import * as actions from 'aws-cdk-lib/aws-cloudwatch-actions';
import * as path from 'path';
import { Construct } from 'constructs';

export interface BondSpreadsStackProps extends cdk.StackProps {
  stage: string;
  table: dynamodb.ITable;
  bucket: s3.IBucket;
  distribution: cloudfront.IDistribution;
  alertTopic: sns.ITopic;
  ssmPrefix: string;
}

export class BondSpreadsStack extends cdk.Stack {
  public readonly ingestLambda: lambda.Function;
  public readonly backfillLambda: lambda.Function;
  public readonly monthlyRule: events.Rule;

  constructor(scope: Construct, id: string, props: BondSpreadsStackProps) {
    super(scope, id, props);

    // Common environment variables for all Lambdas
    const commonEnv = {
      STAGE: props.stage,
      TABLE_NAME: props.table.tableName,
      BUCKET_NAME: props.bucket.bucketName,
      DISTRIBUTION_ID: props.distribution.distributionId,
      SSM_PREFIX: props.ssmPrefix,
      FEATURE: 'bond-spreads',
      DATA_PREFIX: 'data/bond-spreads',
    };

    // Path to backend code
    const backendPath = path.join(__dirname, '../../../../backend');

    // Ingest Lambda - runs monthly to fetch latest data
    this.ingestLambda = new lambda.Function(this, 'IngestLambda', {
      functionName: `fm-${props.stage}-bond-spreads-ingest`,
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: 'features.bond_spreads.handlers.ingest.handler',
      code: lambda.Code.fromAsset(backendPath),
      memorySize: 128,
      timeout: cdk.Duration.minutes(1),
      environment: commonEnv,
    });

    // Backfill Lambda - runs once on first deploy to populate historical data
    this.backfillLambda = new lambda.Function(this, 'BackfillLambda', {
      functionName: `fm-${props.stage}-bond-spreads-backfill`,
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: 'features.bond_spreads.handlers.backfill.handler',
      code: lambda.Code.fromAsset(backendPath),
      memorySize: 128,
      timeout: cdk.Duration.minutes(1),
      environment: commonEnv,
    });

    // Grant permissions to both Lambdas
    [this.ingestLambda, this.backfillLambda].forEach(fn => {
      // DynamoDB read/write
      props.table.grantReadWriteData(fn);

      // S3 put for JSON files
      props.bucket.grantPut(fn);

      // CloudFront invalidation
      fn.addToRolePolicy(new iam.PolicyStatement({
        actions: ['cloudfront:CreateInvalidation'],
        resources: [`arn:aws:cloudfront::${this.account}:distribution/${props.distribution.distributionId}`],
      }));

      // SSM parameter read
      fn.addToRolePolicy(new iam.PolicyStatement({
        actions: ['ssm:GetParameter', 'ssm:GetParameters', 'ssm:GetParametersByPath'],
        resources: [`arn:aws:ssm:${this.region}:${this.account}:parameter${props.ssmPrefix}/*`],
      }));
    });

    // EventBridge rule - 1st of every month at 08:00 UTC
    this.monthlyRule = new events.Rule(this, 'MonthlyRule', {
      ruleName: `fm-${props.stage}-bond-spreads-monthly`,
      description: 'Triggers bond spreads ingest on the 1st of every month',
      schedule: events.Schedule.expression('cron(0 8 1 * ? *)'),
    });

    this.monthlyRule.addTarget(new targets.LambdaFunction(this.ingestLambda));

    // Custom Resource to trigger backfill on first deploy
    // The backfill handler should check if data exists and skip if populated
    const backfillProvider = new cr.Provider(this, 'BackfillProvider', {
      onEventHandler: this.backfillLambda,
    });

    new cdk.CustomResource(this, 'TriggerBackfill', {
      serviceToken: backfillProvider.serviceToken,
      properties: {
        // Add version to prevent re-triggering on unrelated updates
        Version: '1.0.0',
      },
    });

    // =========================================================================
    // CloudWatch Alarms
    // =========================================================================

    this.createLambdaAlarms(this.ingestLambda, 60, props.alertTopic, props.stage);
    this.createLambdaAlarms(this.backfillLambda, 60, props.alertTopic, props.stage);

    // =========================================================================
    // Outputs
    // =========================================================================

    new cdk.CfnOutput(this, 'IngestLambdaArn', {
      value: this.ingestLambda.functionArn,
      description: 'Ingest Lambda ARN',
    });

    new cdk.CfnOutput(this, 'BackfillLambdaArn', {
      value: this.backfillLambda.functionArn,
      description: 'Backfill Lambda ARN',
    });

    new cdk.CfnOutput(this, 'MonthlyRuleName', {
      value: this.monthlyRule.ruleName,
      description: 'EventBridge rule name',
    });
  }

  /**
   * Create CloudWatch alarms for a Lambda function
   */
  private createLambdaAlarms(
    lambdaFn: lambda.Function,
    timeoutSeconds: number,
    alertTopic: sns.ITopic,
    stage: string
  ): void {
    // Error alarm - any errors trigger alert
    const errorAlarm = new cloudwatch.Alarm(this, `${lambdaFn.node.id}ErrorAlarm`, {
      alarmName: `fm-${stage}-${lambdaFn.node.id}-errors`,
      metric: lambdaFn.metricErrors({
        period: cdk.Duration.minutes(1),
      }),
      threshold: 0,
      evaluationPeriods: 1,
      comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
      alarmDescription: `Errors in ${lambdaFn.functionName}`,
      treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
    });
    errorAlarm.addAlarmAction(new actions.SnsAction(alertTopic));

    // Duration alarm - > 80% of timeout
    const durationAlarm = new cloudwatch.Alarm(this, `${lambdaFn.node.id}DurationAlarm`, {
      alarmName: `fm-${stage}-${lambdaFn.node.id}-duration`,
      metric: lambdaFn.metricDuration({
        period: cdk.Duration.minutes(1),
        statistic: 'Maximum',
      }),
      threshold: timeoutSeconds * 1000 * 0.8, // 80% of timeout in milliseconds
      evaluationPeriods: 1,
      comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
      alarmDescription: `Duration warning for ${lambdaFn.functionName} (>80% of timeout)`,
      treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
    });
    durationAlarm.addAlarmAction(new actions.SnsAction(alertTopic));
  }
}
