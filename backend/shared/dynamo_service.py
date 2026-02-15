"""Generic DynamoDB operations for Financial Monitor."""

import boto3
from typing import Any
from aws_lambda_powertools import Logger
from boto3.dynamodb.conditions import Key, Attr

logger = Logger()


class DynamoService:
    """Service for DynamoDB operations."""

    def __init__(self, table_name: str, region: str = "eu-central-1"):
        """Initialize DynamoDB service with table resource.

        Args:
            table_name: Name of the DynamoDB table
            region: AWS region (default: eu-central-1)
        """
        dynamodb = boto3.resource('dynamodb', region_name=region)
        self.table = dynamodb.Table(table_name)
        self.table_name = table_name

    def put_item(
        self,
        pk: str,
        sk: str,
        attributes: dict,
        gsi1pk: str | None = None,
        gsi1sk: float | int | None = None
    ) -> None:
        """Put item with primary and optional GSI keys.

        Args:
            pk: Partition key value
            sk: Sort key value
            attributes: Additional attributes to store
            gsi1pk: Optional GSI1 partition key
            gsi1sk: Optional GSI1 sort key (numeric)
        """
        item = {
            'pk': pk,
            'sk': sk,
            **attributes
        }
        if gsi1pk is not None:
            item['gsi1pk'] = gsi1pk
        if gsi1sk is not None:
            item['gsi1sk'] = gsi1sk

        logger.info("Putting item", extra={"pk": pk, "sk": sk})
        self.table.put_item(Item=item)

    def batch_put_items(self, items: list[dict]) -> None:
        """Batch write items to the table.

        Automatically handles batching in groups of 25.

        Args:
            items: List of complete item dicts with pk, sk, and attributes
        """
        logger.info(f"Batch putting {len(items)} items")

        with self.table.batch_writer() as batch:
            for item in items:
                batch.put_item(Item=item)

    def query_by_pk(
        self,
        pk: str,
        sk_begins_with: str | None = None,
        sk_between: tuple[str, str] | None = None,
        limit: int | None = None,
        ascending: bool = True
    ) -> list[dict]:
        """Query items by partition key with optional SK filters.

        Args:
            pk: Partition key value
            sk_begins_with: Optional SK prefix filter
            sk_between: Optional SK range filter (start, end)
            limit: Optional maximum number of items to return
            ascending: Sort order by SK (default: True)

        Returns:
            List of matching items
        """
        key_condition = Key('pk').eq(pk)

        if sk_begins_with:
            key_condition = key_condition & Key('sk').begins_with(sk_begins_with)
        elif sk_between:
            start, end = sk_between
            key_condition = key_condition & Key('sk').between(start, end)

        query_params = {
            'KeyConditionExpression': key_condition,
            'ScanIndexForward': ascending
        }

        if limit:
            query_params['Limit'] = limit

        logger.info("Querying by PK", extra={"pk": pk})
        response = self.table.query(**query_params)

        return response.get('Items', [])

    def query_gsi1(
        self,
        gsi1pk: str,
        ascending: bool = False,
        limit: int | None = None
    ) -> list[dict]:
        """Query items using GSI1 index.

        Args:
            gsi1pk: GSI1 partition key value
            ascending: Sort by gsi1sk ascending (default: False for descending)
            limit: Optional maximum number of items to return

        Returns:
            List of matching items sorted by gsi1sk
        """
        query_params = {
            'IndexName': 'GSI1',
            'KeyConditionExpression': Key('gsi1pk').eq(gsi1pk),
            'ScanIndexForward': ascending
        }

        if limit:
            query_params['Limit'] = limit

        logger.info("Querying GSI1", extra={"gsi1pk": gsi1pk})
        response = self.table.query(**query_params)

        return response.get('Items', [])

    def get_item(self, pk: str, sk: str) -> dict | None:
        """Get single item by primary key.

        Args:
            pk: Partition key value
            sk: Sort key value

        Returns:
            Item dict if found, None otherwise
        """
        response = self.table.get_item(
            Key={'pk': pk, 'sk': sk}
        )

        return response.get('Item')

    def item_exists(self, pk: str, sk: str) -> bool:
        """Check if item exists without fetching full item.

        Args:
            pk: Partition key value
            sk: Sort key value

        Returns:
            True if item exists, False otherwise
        """
        response = self.table.get_item(
            Key={'pk': pk, 'sk': sk},
            ProjectionExpression='pk'
        )

        return 'Item' in response

    def has_items_with_prefix(self, pk_prefix: str) -> bool:
        """Check if any items exist with the given PK prefix.

        Uses scan with limit=1 for efficiency.

        Args:
            pk_prefix: Partition key prefix to search for

        Returns:
            True if at least one item exists with this prefix
        """
        response = self.table.scan(
            FilterExpression=Attr('pk').begins_with(pk_prefix),
            Limit=1
        )

        return len(response.get('Items', [])) > 0

    def delete_item(self, pk: str, sk: str) -> None:
        """Delete single item by primary key.

        Args:
            pk: Partition key value
            sk: Sort key value
        """
        logger.info("Deleting item", extra={"pk": pk, "sk": sk})
        self.table.delete_item(
            Key={'pk': pk, 'sk': sk}
        )
