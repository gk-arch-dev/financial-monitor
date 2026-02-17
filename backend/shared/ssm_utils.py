"""SSM parameter reading and kill switch utilities."""

from aws_lambda_powertools import Logger

from shared.aws_config import create_client

logger = Logger()


def get_parameter(name: str) -> str:
    """Read SSM parameter (non-encrypted).

    Args:
        name: Full parameter name (e.g., '/fm/box/alert-email')

    Returns:
        Parameter value as string
    """
    ssm = create_client('ssm')
    response = ssm.get_parameter(Name=name)
    return response['Parameter']['Value']


def get_secure_parameter(name: str) -> str:
    """Read SSM SecureString parameter (decrypted).

    Args:
        name: Full parameter name (e.g., '/fm/box/features/bond-spreads/fred-api-key')

    Returns:
        Decrypted parameter value as string
    """
    ssm = create_client('ssm')
    response = ssm.get_parameter(Name=name, WithDecryption=True)
    return response['Parameter']['Value']


def is_kill_switch_active(ssm_prefix: str) -> bool:
    """Check if kill switch is enabled.

    Args:
        ssm_prefix: SSM parameter prefix (e.g., '/fm/box')

    Returns:
        True if kill switch is active, False otherwise
    """
    param_name = f"{ssm_prefix}/kill-switch"
    try:
        value = get_parameter(param_name)
        return value.lower() == 'true'
    except Exception as e:
        logger.warning("Failed to read kill switch, defaulting to False", extra={"error": str(e)})
        return False
