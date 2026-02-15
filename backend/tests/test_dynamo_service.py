"""Tests for DynamoService."""

import pytest
from shared.dynamo_service import DynamoService


def test_put_and_get_item(dynamodb_table):
    """Test put_item and get_item roundtrip."""
    service = DynamoService(table_name='test-table')

    service.put_item(
        pk='TEST#1',
        sk='A',
        attributes={'data': 'value'},
        gsi1pk='GSI#1',
        gsi1sk=100
    )

    item = service.get_item('TEST#1', 'A')
    assert item is not None
    assert item['pk'] == 'TEST#1'
    assert item['sk'] == 'A'
    assert item['data'] == 'value'
    assert item['gsi1pk'] == 'GSI#1'
    assert item['gsi1sk'] == 100


def test_get_item_not_found(dynamodb_table):
    """Test get_item returns None for missing item."""
    service = DynamoService(table_name='test-table')
    item = service.get_item('MISSING#1', 'A')
    assert item is None


def test_query_by_pk(dynamodb_table):
    """Test query_by_pk returns all items for a partition key."""
    service = DynamoService(table_name='test-table')

    # Insert multiple items with same PK
    service.put_item('PK#1', 'A', {'value': 1})
    service.put_item('PK#1', 'B', {'value': 2})
    service.put_item('PK#1', 'C', {'value': 3})
    service.put_item('PK#2', 'A', {'value': 4})

    results = service.query_by_pk('PK#1')
    assert len(results) == 3
    assert results[0]['sk'] == 'A'
    assert results[2]['sk'] == 'C'


def test_query_gsi1(dynamodb_table):
    """Test query_gsi1 returns sorted results."""
    service = DynamoService(table_name='test-table')

    # Insert with GSI values
    service.put_item('PK#1', 'A', {'value': 1}, gsi1pk='GSI#PERIOD', gsi1sk=100)
    service.put_item('PK#2', 'A', {'value': 2}, gsi1pk='GSI#PERIOD', gsi1sk=200)
    service.put_item('PK#3', 'A', {'value': 3}, gsi1pk='GSI#PERIOD', gsi1sk=150)

    # Query descending (default for spreads)
    results = service.query_gsi1('GSI#PERIOD', ascending=False)
    assert len(results) == 3
    assert results[0]['gsi1sk'] == 200  # Highest first
    assert results[2]['gsi1sk'] == 100  # Lowest last


def test_batch_put_items(dynamodb_table):
    """Test batch_put_items writes all items."""
    service = DynamoService(table_name='test-table')

    items = [
        {'pk': f'BATCH#{i}', 'sk': 'A', 'value': i}
        for i in range(30)  # Test > 25 items (batch limit)
    ]

    service.batch_put_items(items)

    # Verify all items were written
    for i in range(30):
        item = service.get_item(f'BATCH#{i}', 'A')
        assert item is not None
        assert item['value'] == i


def test_item_exists(dynamodb_table):
    """Test item_exists check."""
    service = DynamoService(table_name='test-table')

    assert not service.item_exists('PK#1', 'A')

    service.put_item('PK#1', 'A', {'value': 1})

    assert service.item_exists('PK#1', 'A')
    assert not service.item_exists('PK#1', 'B')


def test_has_items_with_prefix(dynamodb_table):
    """Test has_items_with_prefix scan."""
    service = DynamoService(table_name='test-table')

    assert not service.has_items_with_prefix('BS#')

    service.put_item('BS#COUNTRY#US', '2025-01', {'value': 1})

    assert service.has_items_with_prefix('BS#')
    assert not service.has_items_with_prefix('FX#')


def test_delete_item(dynamodb_table):
    """Test delete_item removes item."""
    service = DynamoService(table_name='test-table')

    service.put_item('PK#1', 'A', {'value': 1})
    assert service.item_exists('PK#1', 'A')

    service.delete_item('PK#1', 'A')
    assert not service.item_exists('PK#1', 'A')
