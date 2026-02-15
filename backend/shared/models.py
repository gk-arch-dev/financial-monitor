"""Base dataclasses for Financial Monitor."""

from dataclasses import dataclass, field
from typing import Any
from datetime import datetime


@dataclass
class DynamoRecord:
    """Base class for DynamoDB records with GSI support."""
    pk: str
    sk: str
    gsi1pk: str | None = None
    gsi1sk: float | int | None = None
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class MetaRecord:
    """Metadata record for tracking ingestion state."""
    pk: str  # "{FEATURE_PREFIX}#META"
    sk: str  # "LAST_INGEST" or "LAST_BACKFILL"
    last_updated: datetime | None = None

    def to_dynamo_item(self) -> dict:
        """Convert to DynamoDB item format."""
        item = {
            'pk': self.pk,
            'sk': self.sk,
        }
        if self.last_updated:
            item['last_updated'] = self.last_updated.isoformat()
        return item
