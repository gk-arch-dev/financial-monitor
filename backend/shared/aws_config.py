"""AWS client configuration supporting LocalStack and real AWS."""

import os
import boto3
from typing import Any


def get_endpoint_url() -> str | None:
    """Get LocalStack endpoint URL if configured.

    Returns:
        LocalStack endpoint URL if AWS_ENDPOINT_URL is set, None otherwise.
    """
    return os.environ.get("AWS_ENDPOINT_URL") or os.environ.get("LOCALSTACK_ENDPOINT")


def get_aws_config() -> dict[str, Any]:
    """Get boto3 client/resource configuration.

    Returns configuration dict that can be unpacked into boto3 calls:
        dynamodb = boto3.resource('dynamodb', **get_aws_config())

    When AWS_ENDPOINT_URL is set (LocalStack), uses that endpoint
    with test credentials. Otherwise uses standard AWS credentials.

    Returns:
        Configuration dict for boto3 client/resource initialization.
    """
    config: dict[str, Any] = {
        "region_name": os.environ.get("AWS_REGION", "eu-central-1"),
    }

    endpoint_url = get_endpoint_url()
    if endpoint_url:
        config["endpoint_url"] = endpoint_url
        # LocalStack doesn't require real credentials
        config["aws_access_key_id"] = os.environ.get("AWS_ACCESS_KEY_ID", "test")
        config["aws_secret_access_key"] = os.environ.get("AWS_SECRET_ACCESS_KEY", "test")

    return config


def create_client(service: str, **kwargs: Any) -> Any:
    """Create boto3 client with proper configuration.

    Args:
        service: AWS service name (e.g., 's3', 'dynamodb', 'ssm')
        **kwargs: Additional arguments to pass to boto3.client()

    Returns:
        Configured boto3 client.
    """
    config = get_aws_config()
    config.update(kwargs)
    return boto3.client(service, **config)


def create_resource(service: str, **kwargs: Any) -> Any:
    """Create boto3 resource with proper configuration.

    Args:
        service: AWS service name (e.g., 's3', 'dynamodb')
        **kwargs: Additional arguments to pass to boto3.resource()

    Returns:
        Configured boto3 resource.
    """
    config = get_aws_config()
    config.update(kwargs)
    return boto3.resource(service, **config)
