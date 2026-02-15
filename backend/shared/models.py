"""Base dataclasses for Financial Monitor."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class BaseRecord:
    """Base class for DynamoDB records."""

    pk: str
    sk: str


@dataclass
class MetaRecord(BaseRecord):
    """Metadata record for tracking ingestion state."""

    last_ingest: datetime | None = None
    last_backfill: datetime | None = None
