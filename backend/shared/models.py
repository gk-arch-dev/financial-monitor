"""Base dataclasses for Financial Monitor."""

from dataclasses import dataclass, field
from typing import Any
from datetime import datetime


@dataclass
class DynamoRecord:
    """Base class for DynamoDB records with GSI support."""
    PK: str
    SK: str
    GSI1PK: str | None = None
    GSI1SK: float | int | None = None
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class MetaRecord:
    """Metadata record for tracking ingestion state."""
    PK: str  # "{FEATURE_PREFIX}#META"
    SK: str  # "LAST_INGEST" or "LAST_BACKFILL"
    last_updated: datetime | None = None

    def to_dynamo_item(self) -> dict:
        """Convert to DynamoDB item format."""
        item = {
            'PK': self.PK,
            'SK': self.SK,
        }
        if self.last_updated:
            item['last_updated'] = self.last_updated.isoformat()
        return item
