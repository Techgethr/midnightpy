import pytest
import asyncio
from unittest.mock import Mock, patch
from datetime import datetime

from midnightpy import BlockchainClient
from midnightpy.exceptions import ConnectionError, SubscriptionError
from midnightpy.types import Block, Transaction, ContractAction, ContractCall

# Mock data for testing
MOCK_BLOCK_DATA = {
    "hash": "0x123",
    "height": 100,
    "protocolVersion": 1,
    "timestamp": 1234567890,
    "author": "0x456",
    "parent": {
        "hash": "0x789",
        "height": 99
    },
    "transactions": [{
        "hash": "0xabc",
        "protocolVersion": 1,
        "applyStage": "APPLIED",
        "identifiers": ["0xdef"],
        "raw": "0xraw",
        "merkleTreeRoot": "0xroot"
    }]
}

MOCK_CONTRACT_ACTION_DATA = {
    "address": "0x123",
    "state": "0xstate",
    "chainState": "0xchainState",
    "entryPoint": "0xentry",
    "transaction": {
        "hash": "0xabc",
        "protocolVersion": 1,
        "applyStage": "APPLIED",
        "identifiers": ["0xdef"],
        "raw": "0xraw",
        "merkleTreeRoot": "0xroot"
    }
}

@pytest.fixture
async def client():
    """Create a BlockchainClient instance for testing."""
    client = BlockchainClient(
        http_url="http://test.example/graphql",
        ws_url="ws://test.example/graphql"
    )
    yield client
    # Cleanup
    if client.http_transport:
        await client.http_transport.close()
    if client.ws_transport:
        await client.ws_transport.close()

@pytest.mark.asyncio
async def test_client_initialization():
    """Test client initialization with valid URLs."""
    client = BlockchainClient(
        http_url="http://test.example/graphql",
        ws_url="ws://test.example/graphql"
    )
    assert client.http_client is not None
    assert client.ws_client is not None

@pytest.mark.asyncio
async def test_client_initialization_invalid_url():
    """Test client initialization with invalid URL."""
    with pytest.raises(ConnectionError):
        BlockchainClient(http_url="invalid-url")

@pytest.mark.asyncio
async def test_get_latest_block(client):
    """Test getting the latest block."""
    with patch.object(client, '_execute_with_retry') as mock_execute:
        mock_execute.return_value = {"block": MOCK_BLOCK_DATA}
        
        block = await client.get_latest_block()
        
        assert isinstance(block, Block)
        assert block.hash == "0x123"
        assert block.height == 100
        assert isinstance(block.datetime, datetime)
        assert len(block.transactions) == 1
        assert block.parent is not None
        assert block.parent.hash == "0x789"

@pytest.mark.asyncio
async def test_get_block_by_hash(client):
    """Test getting a block by hash."""
    with patch.object(client, '_execute_with_retry') as mock_execute:
        mock_execute.return_value = {"block": MOCK_BLOCK_DATA}
        
        block = await client.get_block_by_hash("0x123")
        
        assert isinstance(block, Block)
        assert block.hash == "0x123"
        assert len(block.transactions) == 1

@pytest.mark.asyncio
async def test_get_block_by_height(client):
    """Test getting a block by height."""
    with patch.object(client, '_execute_with_retry') as mock_execute:
        mock_execute.return_value = {"block": MOCK_BLOCK_DATA}
        
        block = await client.get_block_by_height(100)
        
        assert isinstance(block, Block)
        assert block.height == 100

@pytest.mark.asyncio
async def test_get_contract_action(client):
    """Test getting a contract action."""
    with patch.object(client, '_execute_with_retry') as mock_execute:
        mock_execute.return_value = {"contractAction": MOCK_CONTRACT_ACTION_DATA}
        
        action = await client.get_contract_action("0x123")
        
        assert isinstance(action, ContractCall)
        assert action.address == "0x123"
        assert action.entry_point == "0xentry"

@pytest.mark.asyncio
async def test_connect_wallet(client):
    """Test connecting a wallet."""
    with patch.object(client, '_execute_with_retry') as mock_execute:
        mock_execute.return_value = {"connect": "0xsession"}
        
        session_id = await client.connect_wallet("viewing-key")
        assert session_id == "0xsession"

@pytest.mark.asyncio
async def test_disconnect_wallet(client):
    """Test disconnecting a wallet."""
    with patch.object(client, '_execute_with_retry') as mock_execute:
        mock_execute.return_value = {"disconnect": None}
        
        result = await client.disconnect_wallet("0xsession")
        assert result is True

@pytest.mark.asyncio
async def test_subscribe_to_blocks_no_ws(client):
    """Test subscribing to blocks without WebSocket URL."""
    client.ws_client = None
    with pytest.raises(SubscriptionError):
        async for _ in client.subscribe_to_blocks():
            pass

@pytest.mark.asyncio
async def test_subscribe_to_blocks(client):
    """Test subscribing to blocks."""
    mock_subscription = Mock()
    mock_subscription.__aiter__.return_value = [{"blocks": MOCK_BLOCK_DATA}]
    
    with patch.object(client.ws_client, 'subscribe_async', return_value=mock_subscription):
        async for block in client.subscribe_to_blocks():
            assert isinstance(block, Block)
            assert block.hash == "0x123"
            break

@pytest.mark.asyncio
async def test_retry_logic(client):
    """Test retry logic for failed requests."""
    mock_error = Exception("Test error")
    
    with patch.object(client.http_client, 'execute_async') as mock_execute:
        mock_execute.side_effect = [mock_error, mock_error, {"block": MOCK_BLOCK_DATA}]
        
        block = await client.get_latest_block()
        assert isinstance(block, Block)
        assert mock_execute.call_count == 3

@pytest.mark.asyncio
async def test_parse_transaction(client):
    """Test transaction parsing."""
    transaction = client._parse_transaction(MOCK_BLOCK_DATA["transactions"][0])
    assert isinstance(transaction, Transaction)
    assert transaction.hash == "0xabc"
    assert transaction.protocol_version == 1
    assert transaction.apply_stage == "APPLIED"

@pytest.mark.asyncio
async def test_parse_contract_action(client):
    """Test contract action parsing."""
    action = client._parse_contract_action(MOCK_CONTRACT_ACTION_DATA)
    assert isinstance(action, ContractCall)
    assert action.address == "0x123"
    assert action.state == "0xstate"
    assert action.entry_point == "0xentry" 