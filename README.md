# MidnightPy

A Python SDK for interacting with the [Midnight blockchain network](https://midnight.network/).

## Features

- Full async/await support
- Static typing for better IDE integration
- Robust error handling with custom exceptions
- Automatic retries for failed queries
- Input data validation
- WebSocket support for real-time updates
- Comprehensive documentation
- Extensive test coverage

## Installation

1. Clone this repository
2. Install the dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Client Initialization

```python
import asyncio
from midnightpy import BlockchainClient

async def main():
    # Initialize the client with your GraphQL endpoints
    client = BlockchainClient(
        http_url="http://your-graphql-endpoint/graphql",
        ws_url="ws://your-graphql-endpoint/graphql",  # Optional, for subscriptions
        timeout=30,  # Timeout in seconds
        retry_attempts=3  # Number of retry attempts for failed queries
    )
```

### Basic Queries

```python
    # Get the latest block
    latest_block = await client.get_latest_block()
    print(f"Latest block height: {latest_block.height}")
    print(f"Block timestamp: {latest_block.datetime}")

    # Get a block by its hash
    block = await client.get_block_by_hash("0x123...")
    if block:
        print(f"Found block at height: {block.height}")
        if block.parent:
            print(f"Parent block hash: {block.parent.hash}")

    # Get a block by height
    block = await client.get_block_by_height(12345)
    if block:
        print(f"Block hash: {block.hash}")
```

### Contract Interactions

```python
    # Get contract action
    action = await client.get_contract_action("0x789...")
    if action:
        print(f"Contract state: {action.state}")

    # Get contract action at specific block
    action = await client.get_contract_action_at_block(
        address="0x789...",
        block_hash="0x123..."
    )
    if action:
        print(f"Historical contract state: {action.state}")

    # Get transactions by identifier
    transactions = await client.get_transactions_by_identifier("0x456...")
    for tx in transactions:
        print(f"Transaction hash: {tx.hash}")
```

### Wallet Operations

```python
    # Connect wallet
    session_id = await client.connect_wallet("your-viewing-key")
    print(f"Connected with session: {session_id}")

    # Subscribe to wallet events
    async for event in client.subscribe_to_wallet(
        session_id,
        send_progress_updates=True
    ):
        if isinstance(event, ProgressUpdate):
            print(f"Sync progress: {event.highest_relevant_index}")
        else:  # RelevantTransaction
            print(f"New transaction: {event.transaction.hash}")

    # Disconnect wallet
    await client.disconnect_wallet(session_id)
```

### Real-time Subscriptions

```python
    # Subscribe to new blocks
    async for block in client.subscribe_to_blocks():
        print(f"New block received! Height: {block.height}")

    # Subscribe to contract actions
    async for action in client.subscribe_to_contract_actions("0x789..."):
        print(f"New contract action! State: {action.state}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Error Handling

```python
from midnightpy.exceptions import (
    BlockchainSDKException,
    GraphQLError,
    ConnectionError,
    ValidationError,
    SubscriptionError
)

async def main():
    try:
        client = BlockchainClient(...)
        block = await client.get_block_by_hash("invalid_hash")
    except ValidationError as e:
        print(f"Validation error: {e}")
    except GraphQLError as e:
        print(f"GraphQL error: {e}")
        print(f"Specific errors: {e.errors}")
    except ConnectionError as e:
        print(f"Connection error: {e}")
    except SubscriptionError as e:
        print(f"Subscription error: {e}")
    except BlockchainSDKException as e:
        print(f"General SDK error: {e}")
```

## Testing

The SDK includes a comprehensive test suite using pytest. To run the tests:

1. Install test dependencies:
```bash
pip install -r requirements-dev.txt
```

2. Run the tests:
```bash
pytest tests/
```

The test suite includes:
- Unit tests for all SDK functionality
- Integration tests for GraphQL queries
- Mock tests for network operations
- Error handling tests
- Subscription tests
- Parsing tests for blockchain data

## API Reference

### BlockchainClient

The main class for interacting with the blockchain network.

#### Methods

- `get_latest_block() -> Block`
  - Returns the latest block from the blockchain

- `get_block_by_hash(block_hash: str) -> Optional[Block]`
  - Returns a block by its hash, or None if not found

- `get_block_by_height(height: int) -> Optional[Block]`
  - Returns a block by its height, or None if not found

- `get_contract_action(address: str) -> Optional[ContractAction]`
  - Returns the latest contract action

- `get_contract_action_at_block(address: str, block_hash: str) -> Optional[ContractAction]`
  - Returns a contract action at a specific block

- `get_transactions_by_identifier(identifier: str) -> List[Transaction]`
  - Returns transactions matching the identifier

- `connect_wallet(viewing_key: str) -> str`
  - Connects a wallet and returns a session ID

- `disconnect_wallet(session_id: str) -> bool`
  - Disconnects a wallet session

- `subscribe_to_blocks(start_height: Optional[int] = None)`
  - Generator that yields new blocks as they are created

- `subscribe_to_contract_actions(address: str, start_block_height: Optional[int] = None)`
  - Generator that yields contract actions

- `subscribe_to_wallet(session_id: str, start_index: Optional[int] = None, send_progress_updates: bool = False)`
  - Generator that yields wallet events

### Data Models

- `Block`
  - `hash: str`
  - `height: int`
  - `protocol_version: int`
  - `timestamp: int`
  - `author: Optional[str]`
  - `parent: Optional[Block]`
  - `transactions: List[Transaction]`
  - `datetime: datetime` (property)

- `Transaction`
  - `hash: str`
  - `protocol_version: int`
  - `apply_stage: str`
  - `identifiers: List[str]`
  - `raw: str`
  - `merkle_tree_root: str`
  - `contract_actions: List[ContractAction]`
  - `block: Optional[Block]`

- `ContractAction` (base class)
  - `address: str`
  - `state: str`
  - `chain_state: str`
  - `transaction: Transaction`

- `ContractCall` (extends ContractAction)
  - Additional fields:
    - `entry_point: str`
    - `deploy: ContractDeploy`

- `ContractDeploy` (extends ContractAction)
- `ContractUpdate` (extends ContractAction)

## License

MIT 