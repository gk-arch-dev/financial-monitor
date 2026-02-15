"""SSM parameter reading and kill switch utilities."""

import boto3
from aws_lambda_powertools import Logger

logger = Logger()


def get_parameter(name: str, region: str = "eu-central-1") -> str:
    """Read SSM parameter (non-encrypted).

    Args:
        name: Full parameter name (e.g., '/fm/box/alert-email')
        region: AWS region (default: eu-central-1)

    Returns:
        Parameter value as string
    """
    ssm = boto3.client('ssm', region_name=region)
    response = ssm.get_parameter(Name=name)
    return response['Parameter']['Value']


def get_secure_parameter(name: str, region: str = "eu-central-1") -> str:
    """Read SSM SecureString parameter (decrypted).

    Args:
        name: Full parameter name (e.g., '/fm/box/features/bond-spreads/fred-api-key')
        region: AWS region (default: eu-central-1)

    Returns:
        Decrypted parameter value as string
    """
    ssm = boto3.client('ssm', region_name=region)
    response = ssm.get_parameter(Name=name, WithDecryption=True)
    return response['Parameter']['Value']


def is_kill_switch_active(ssm_prefix: str, region: str = "eu-central-1") -> bool:
    """Check if kill switch is enabled.

    Args:
        ssm_prefix: SSM parameter prefix (e.g., '/fm/box')
        region: AWS region (default: eu-central-1)

    Returns:
        True if kill switch is active, False otherwise
    """
    param_name = f"{ssm_prefix}/kill-switch"
    try:
        value = get_parameter(param_name, region)
        return value.lower() == 'true'
    except Exception as e:
        logger.warning("Failed to read kill switch, defaulting to False", extra={"error": str(e)})
        return False
