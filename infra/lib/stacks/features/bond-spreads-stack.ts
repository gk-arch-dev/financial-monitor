import * as cdk from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as cloudfront from 'aws-cdk-lib/aws-cloudfront';
import * as sns from 'aws-cdk-lib/aws-sns';
import * as scheduler from 'aws-cdk-lib/aws-scheduler';
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
  public readonly monthlySchedule: scheduler.CfnSchedule;

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

    // Lambda Layer with dependencies
    const depsLayer = new lambda.LayerVersion(this, 'DependenciesLayer', {
      code: lambda.Code.fromAsset(path.join(backendPath, 'lambda-layer')),
      compatibleRuntimes: [lambda.Runtime.PYTHON_3_12],
      description: 'Python dependencies for bond spreads handlers',
    });

    // Ingest Lambda - runs monthly to fetch latest data
    this.ingestLambda = new lambda.Function(this, 'IngestLambda', {
      functionName: `fm-${props.stage}-bond-spreads-ingest`,
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: 'features.bond_spreads.handlers.ingest.handler',
      code: lambda.Code.fromAsset(backendPath, {
        exclude: ['lambda-layer', 'tests', '*.pyc', '__pycache__', '.pytest_cache'],
      }),
      layers: [depsLayer],
      memorySize: 256,
      timeout: cdk.Duration.minutes(5),
      environment: commonEnv,
    });

    // Backfill Lambda - runs once on first deploy to populate historical data
    this.backfillLambda = new lambda.Function(this, 'BackfillLambda', {
      functionName: `fm-${props.stage}-bond-spreads-backfill`,
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: 'features.bond_spreads.handlers.backfill.handler',
      code: lambda.Code.fromAsset(backendPath, {
        exclude: ['lambda-layer', 'tests', '*.pyc', '__pycache__', '.pytest_cache'],
      }),
      layers: [depsLayer],
      memorySize: 512,
      timeout: cdk.Duration.minutes(15),
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

    // IAM role for EventBridge Scheduler
    const scheduleRole = new iam.Role(this, 'ScheduleRole', {
      assumedBy: new iam.ServicePrincipal('scheduler.amazonaws.com'),
    });

    this.ingestLambda.grantInvoke(scheduleRole);

    // EventBridge Scheduler - 16th of every month at 08:00 UTC
    this.monthlySchedule = new scheduler.CfnSchedule(this, 'MonthlySchedule', {
      name: `fm-${props.stage}-bond-spreads-monthly`,
      description: 'Triggers bond spreads ingest on the 16th of every month',
      scheduleExpression: 'cron(0 8 16 * ? *)',
      scheduleExpressionTimezone: 'UTC',
      flexibleTimeWindow: {
        mode: 'OFF',
      },
      target: {
        arn: this.ingestLambda.functionArn,
        roleArn: scheduleRole.roleArn,
        retryPolicy: {
          maximumRetryAttempts: 2,
        },
      },
    });

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

    this.createLambdaAlarms(this.ingestLambda, 300, props.alertTopic, props.stage);
    this.createLambdaAlarms(this.backfillLambda, 900, props.alertTopic, props.stage);

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

    new cdk.CfnOutput(this, 'MonthlyScheduleName', {
      value: this.monthlySchedule.name || '',
      description: 'EventBridge schedule name',
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
