"""SSM parameter reading and kill switch utilities."""

import os


def get_ssm_parameter(name: str) -> str:
    """Get a parameter value from SSM.

    Args:
        name: Full parameter name (e.g., /fm/box/kill-switch)

    Returns:
        Parameter value as string
    """
    pass


def is_kill_switch_enabled() -> bool:
    """Check if the kill switch is enabled.

    Returns:
        True if kill switch is enabled, False otherwise
    """
    ssm_prefix = os.environ.get('SSM_PREFIX', '/fm/box')
    # Implementation will check {ssm_prefix}/kill-switch
    pass


def get_feature_config(feature: str) -> dict:
    """Get configuration for a specific feature.

    Args:
        feature: Feature name (e.g., 'bond-spreads')

    Returns:
        Dictionary of feature configuration
    """
    pass
