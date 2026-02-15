import * as cdk from 'aws-cdk-lib';
import * as sns from 'aws-cdk-lib/aws-sns';
import * as subscriptions from 'aws-cdk-lib/aws-sns-subscriptions';
import * as budgets from 'aws-cdk-lib/aws-budgets';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as cloudwatch from 'aws-cdk-lib/aws-cloudwatch';
import * as actions from 'aws-cdk-lib/aws-cloudwatch-actions';
import * as iam from 'aws-cdk-lib/aws-iam';
import { Construct } from 'constructs';

export interface MonitoringStackProps extends cdk.StackProps {
  stage: string;
  alertEmail: string;
  ssmPrefix: string;
}

export class MonitoringStack extends cdk.Stack {
  public readonly alertTopic: sns.Topic;
  private readonly stage: string;

  constructor(scope: Construct, id: string, props: MonitoringStackProps) {
    super(scope, id, props);

    this.stage = props.stage;

    // SNS Topic for alerts
    this.alertTopic = new sns.Topic(this, 'AlertsTopic', {
      topicName: `fm-${props.stage}-alerts`,
      displayName: `Financial Monitor Alerts (${props.stage})`,
    });

    this.alertTopic.addSubscription(
      new subscriptions.EmailSubscription(props.alertEmail)
    );

    // Kill Switch Lambda
    const killSwitchLambda = new lambda.Function(this, 'KillSwitchLambda', {
      functionName: `fm-${props.stage}-kill-switch`,
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: 'index.handler',
      code: lambda.Code.fromInline(`
import boto3
import os
import json

def handler(event, context):
    ssm = boto3.client('ssm')
    sns_client = boto3.client('sns')
    events = boto3.client('events')

    # Set kill switch to true
    ssm.put_parameter(
        Name=os.environ['KILL_SWITCH_PARAM'],
        Value='true',
        Overwrite=True
    )

    # Disable EventBridge rules
    rules = os.environ.get('EVENT_RULES', '').split(',')
    disabled_rules = []
    for rule in rules:
        rule = rule.strip()
        if rule:
            try:
                events.disable_rule(Name=rule)
                disabled_rules.append(rule)
            except Exception as e:
                print(f"Failed to disable rule {rule}: {e}")

    # Send notification
    sns_client.publish(
        TopicArn=os.environ['ALERT_TOPIC'],
        Subject='[CRITICAL] Financial Monitor Kill Switch Activated',
        Message=json.dumps({
            'message': 'Cost limit exceeded. All scheduled tasks have been disabled.',
            'disabled_rules': disabled_rules,
            'stage': os.environ.get('STAGE', 'unknown')
        }, indent=2)
    )

    return {
        'statusCode': 200,
        'body': json.dumps({'disabled_rules': disabled_rules})
    }
      `),
      environment: {
        KILL_SWITCH_PARAM: `${props.ssmPrefix}/kill-switch`,
        ALERT_TOPIC: this.alertTopic.topicArn,
        EVENT_RULES: '', // Will be updated when feature stacks are added
        STAGE: props.stage,
      },
      timeout: cdk.Duration.seconds(30),
    });

    // Grant kill switch Lambda permissions
    killSwitchLambda.addToRolePolicy(new iam.PolicyStatement({
      actions: ['ssm:PutParameter'],
      resources: [`arn:aws:ssm:${this.region}:${this.account}:parameter${props.ssmPrefix}/*`],
    }));

    killSwitchLambda.addToRolePolicy(new iam.PolicyStatement({
      actions: ['events:DisableRule'],
      resources: [`arn:aws:events:${this.region}:${this.account}:rule/fm-${props.stage}-*`],
    }));

    this.alertTopic.grantPublish(killSwitchLambda);

    // AWS Budget
    new budgets.CfnBudget(this, 'MonthlyBudget', {
      budget: {
        budgetName: `fm-${props.stage}-monthly`,
        budgetType: 'COST',
        timeUnit: 'MONTHLY',
        budgetLimit: {
          amount: 15,
          unit: 'USD',
        },
      },
      notificationsWithSubscribers: [
        {
          notification: {
            notificationType: 'ACTUAL',
            comparisonOperator: 'GREATER_THAN',
            threshold: 10,
            thresholdType: 'ABSOLUTE_VALUE',
          },
          subscribers: [{
            subscriptionType: 'SNS',
            address: this.alertTopic.topicArn,
          }],
        },
        {
          notification: {
            notificationType: 'ACTUAL',
            comparisonOperator: 'GREATER_THAN',
            threshold: 15,
            thresholdType: 'ABSOLUTE_VALUE',
          },
          subscribers: [{
            subscriptionType: 'SNS',
            address: this.alertTopic.topicArn,
          }],
        },
      ],
    });

    // Outputs
    new cdk.CfnOutput(this, 'AlertTopicArn', {
      value: this.alertTopic.topicArn,
      description: 'SNS topic ARN for alerts',
    });
  }

  /**
   * Create CloudWatch alarms for a Lambda function
   */
  public createLambdaAlarms(
    lambdaFn: lambda.IFunction,
    timeoutSeconds: number
  ): void {
    // Error alarm - any errors trigger alert
    const errorAlarm = new cloudwatch.Alarm(this, `${lambdaFn.node.id}ErrorAlarm`, {
      alarmName: `fm-${this.stage}-${lambdaFn.node.id}-errors`,
      metric: lambdaFn.metricErrors({
        period: cdk.Duration.minutes(1),
      }),
      threshold: 0,
      evaluationPeriods: 1,
      comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
      alarmDescription: `Errors in ${lambdaFn.functionName}`,
      treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
    });
    errorAlarm.addAlarmAction(new actions.SnsAction(this.alertTopic));

    // Duration alarm - > 80% of timeout
    const durationAlarm = new cloudwatch.Alarm(this, `${lambdaFn.node.id}DurationAlarm`, {
      alarmName: `fm-${this.stage}-${lambdaFn.node.id}-duration`,
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
    durationAlarm.addAlarmAction(new actions.SnsAction(this.alertTopic));
  }
}
