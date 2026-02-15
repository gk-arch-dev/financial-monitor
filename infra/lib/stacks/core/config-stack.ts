import * as cdk from 'aws-cdk-lib';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import { Construct } from 'constructs';

export interface ConfigStackProps extends cdk.StackProps {
  stage: string;
}

// Default configuration values
export const CONFIG_DEFAULTS = {
  alertEmail: 'grzegorz.karolak@outlook.com',
  costLimitWarning: '10',
  costLimitCritical: '15',
};

export class ConfigStack extends cdk.Stack {
  public readonly ssmPrefix: string;
  public readonly alertEmailParam: ssm.StringParameter;
  public readonly alertEmail: string;

  constructor(scope: Construct, id: string, props: ConfigStackProps) {
    super(scope, id, props);

    this.ssmPrefix = `/fm/${props.stage}`;
    this.alertEmail = CONFIG_DEFAULTS.alertEmail;

    // Alert email
    this.alertEmailParam = new ssm.StringParameter(this, 'AlertEmail', {
      parameterName: `${this.ssmPrefix}/alert-email`,
      stringValue: this.alertEmail,
      description: 'Email address for alerts',
    });

    // Cost limit warning threshold
    new ssm.StringParameter(this, 'CostLimitWarning', {
      parameterName: `${this.ssmPrefix}/cost-limit-warning`,
      stringValue: CONFIG_DEFAULTS.costLimitWarning,
      description: 'Cost warning threshold in USD',
    });

    // Cost limit critical threshold
    new ssm.StringParameter(this, 'CostLimitCritical', {
      parameterName: `${this.ssmPrefix}/cost-limit-critical`,
      stringValue: CONFIG_DEFAULTS.costLimitCritical,
      description: 'Cost critical threshold in USD',
    });

    // Kill switch
    new ssm.StringParameter(this, 'KillSwitch', {
      parameterName: `${this.ssmPrefix}/kill-switch`,
      stringValue: 'false',
      description: 'Emergency kill switch to disable all scheduled tasks',
    });

    // FRED API key placeholder
    // Note: CDK cannot create SecureString parameters. Create as String placeholder,
    // then manually update to SecureString with actual API key after deployment.
    new ssm.StringParameter(this, 'FredApiKey', {
      parameterName: `${this.ssmPrefix}/features/bond-spreads/fred-api-key`,
      stringValue: 'DUMMY_KEY_REPLACE_ME',
      description: 'FRED API key - replace with actual SecureString after deployment',
    });
  }
}
