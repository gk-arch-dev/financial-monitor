#!/usr/bin/env python3
"""Invoke Lambda handlers locally with LocalStack backend.

Usage:
    python scripts/local-invoke.py ingest
    python scripts/local-invoke.py backfill
    python scripts/local-invoke.py ingest --event '{"detail": {}}'
"""

import argparse
import json
import os
import sys

# Add backend to path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
sys.path.insert(0, BACKEND_DIR)


def setup_local_environment():
    """Configure environment for LocalStack."""
    os.environ.setdefault("AWS_ENDPOINT_URL", "http://localhost:4566")
    os.environ.setdefault("AWS_REGION", "eu-central-1")
    os.environ.setdefault("AWS_ACCESS_KEY_ID", "test")
    os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "test")
    os.environ.setdefault("STAGE", "local")
    os.environ.setdefault("TABLE_NAME", "fm-local-data")
    os.environ.setdefault("BUCKET_NAME", "fm-local-frontend")
    os.environ.setdefault("DISTRIBUTION_ID", "LOCAL123456")
    os.environ.setdefault("SSM_PREFIX", "/fm/local")
    os.environ.setdefault("FEATURE", "bond-spreads")
    os.environ.setdefault("DATA_PREFIX", "data/bond-spreads")


class MockContext:
    """Mock AWS Lambda context object."""

    function_name = "local-invoke"
    memory_limit_in_mb = 256
    invoked_function_arn = "arn:aws:lambda:eu-central-1:000000000000:function:local"
    aws_request_id = "local-request-id"
    log_stream_name = "local-log-stream"

    def get_remaining_time_in_millis(self):
        return 300000  # 5 minutes


def invoke_handler(handler_path: str, event: dict):
    """Import and invoke a Lambda handler.

    Args:
        handler_path: Dot-separated path to handler (e.g., features.bond_spreads.handlers.ingest.handler)
        event: Event dict to pass to the handler

    Returns:
        Handler return value
    """
    module_path, handler_name = handler_path.rsplit(".", 1)

    # Dynamic import
    module = __import__(module_path, fromlist=[handler_name])
    handler_func = getattr(module, handler_name)

    return handler_func(event, MockContext())


def main():
    parser = argparse.ArgumentParser(
        description="Invoke Lambda handlers locally with LocalStack backend"
    )
    parser.add_argument(
        "handler",
        choices=["ingest", "backfill"],
        help="Handler to invoke",
    )
    parser.add_argument(
        "--event",
        type=str,
        default="{}",
        help="JSON event payload (default: {})",
    )
    parser.add_argument(
        "--event-file",
        type=str,
        help="Path to JSON event file (overrides --event)",
    )

    args = parser.parse_args()

    # Setup environment
    setup_local_environment()

    # Determine handler path
    handlers = {
        "ingest": "features.bond_spreads.handlers.ingest.handler",
        "backfill": "features.bond_spreads.handlers.backfill.handler",
    }
    handler_path = handlers[args.handler]

    # Parse event
    if args.event_file:
        with open(args.event_file) as f:
            event = json.load(f)
    else:
        event = json.loads(args.event)

    print(f"Invoking {handler_path}")
    print(f"Event: {json.dumps(event, indent=2)}")
    print("-" * 60)

    try:
        result = invoke_handler(handler_path, event)
        print("-" * 60)
        print(f"Result: {json.dumps(result, indent=2, default=str)}")
        return 0
    except Exception as e:
        print("-" * 60)
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
