from typing import Optional, List, Dict, Any
import asyncio
from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport
from gql.transport.websockets import WebsocketsTransport

from .types import (
    Block,
    Transaction,
    ContractAction,
    ContractCall,
    ContractDeploy,
    ContractUpdate,
    ProgressUpdate,
    RelevantTransaction,
    WalletSyncEvent
)
from .exceptions import GraphQLError, ConnectionError, SubscriptionError


class BlockchainClient:
    def __init__(
        self,
        http_url: str,
        ws_url: Optional[str] = None,
        timeout: int = 30,
        retry_attempts: int = 3
    ):
        """
        Initialize the blockchain client.
        
        Args:
            http_url: The HTTP URL of the GraphQL endpoint
            ws_url: Optional WebSocket URL for subscriptions
            timeout: Request timeout in seconds
            retry_attempts: Number of retry attempts for failed requests
        """
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        
        try:
            self.http_transport = AIOHTTPTransport(
                url=http_url,
                timeout=timeout
            )
            self.ws_transport = WebsocketsTransport(url=ws_url) if ws_url else None
            self.http_client = Client(transport=self.http_transport)
            self.ws_client = Client(transport=self.ws_transport) if self.ws_transport else None
        except Exception as e:
            raise ConnectionError(f"Failed to initialize client: {str(e)}")

    async def get_latest_block(self) -> Block:
        """Get the latest block from the blockchain."""
        query = gql("""
            query {
                block {
                    hash
                    height
                    protocolVersion
                    timestamp
                    author
                    parent {
                        hash
                        height
                    }
                    transactions {
                        hash
                        protocolVersion
                        applyStage
                        identifiers
                        raw
                        merkleTreeRoot
                    }
                }
            }
        """)
        
        result = await self._execute_with_retry(query)
        return self._parse_block(result["block"])

    async def get_block_by_hash(self, block_hash: str) -> Optional[Block]:
        """Get a block by its hash."""
        query = gql("""
            query($hash: HexEncoded!) {
                block(offset: { hash: $hash }) {
                    hash
                    height
                    protocolVersion
                    timestamp
                    author
                    parent {
                        hash
                        height
                    }
                    transactions {
                        hash
                        protocolVersion
                        applyStage
                        identifiers
                        raw
                        merkleTreeRoot
                    }
                }
            }
        """)
        
        result = await self._execute_with_retry(query, variable_values={"hash": block_hash})
        return self._parse_block(result["block"]) if result["block"] else None

    async def get_block_by_height(self, height: int) -> Optional[Block]:
        """
        Get a block by its height.
        
        Args:
            height: The block height to retrieve
        """
        query = gql("""
            query($height: Int!) {
                block(offset: { height: $height }) {
                    hash
                    height
                    protocolVersion
                    timestamp
                    author
                    parent {
                        hash
                        height
                    }
                    transactions {
                        hash
                        protocolVersion
                        applyStage
                        identifiers
                        raw
                        merkleTreeRoot
                    }
                }
            }
        """)
        
        result = await self._execute_with_retry(query, variable_values={"height": height})
        return self._parse_block(result["block"]) if result["block"] else None

    async def get_contract_action(self, address: str) -> Optional[ContractAction]:
        """Get the latest contract action for a given address."""
        query = gql("""
            query($address: HexEncoded!) {
                contractAction(address: $address) {
                    address
                    state
                    chainState
                    ... on ContractCall {
                        entryPoint
                    }
                    transaction {
                        hash
                        protocolVersion
                        applyStage
                        identifiers
                        raw
                        merkleTreeRoot
                    }
                }
            }
        """)
        
        result = await self._execute_with_retry(query, variable_values={"address": address})
        return self._parse_contract_action(result["contractAction"]) if result["contractAction"] else None

    async def get_contract_action_at_block(self, address: str, block_hash: str) -> Optional[ContractAction]:
        """
        Get a contract action at a specific block.
        
        Args:
            address: The contract address
            block_hash: The block hash to query at
        """
        query = gql("""
            query($address: HexEncoded!, $hash: HexEncoded!) {
                contractAction(
                    address: $address,
                    offset: { blockOffset: { hash: $hash } }
                ) {
                    address
                    state
                    chainState
                    ... on ContractCall {
                        entryPoint
                    }
                    transaction {
                        hash
                        protocolVersion
                        applyStage
                        identifiers
                        raw
                        merkleTreeRoot
                    }
                }
            }
        """)
        
        result = await self._execute_with_retry(
            query,
            variable_values={"address": address, "hash": block_hash}
        )
        return self._parse_contract_action(result["contractAction"]) if result["contractAction"] else None

    async def get_transactions_by_identifier(self, identifier: str) -> List[Transaction]:
        """
        Get transactions by their identifier.
        
        Args:
            identifier: The transaction identifier
        """
        query = gql("""
            query($identifier: HexEncoded!) {
                transactions(offset: { identifier: $identifier }) {
                    hash
                    protocolVersion
                    applyStage
                    identifiers
                    raw
                    merkleTreeRoot
                    block {
                        hash
                        height
                    }
                    contractActions {
                        address
                        state
                        chainState
                        ... on ContractCall {
                            entryPoint
                        }
                    }
                }
            }
        """)
        
        result = await self._execute_with_retry(
            query,
            variable_values={"identifier": identifier}
        )
        return [self._parse_transaction(tx) for tx in result["transactions"]]

    async def connect_wallet(self, viewing_key: str) -> str:
        """
        Connect a wallet using a viewing key.
        
        Args:
            viewing_key: The wallet viewing key
            
        Returns:
            str: The session ID for the connected wallet
        """
        mutation = gql("""
            mutation($viewingKey: ViewingKey!) {
                connect(viewingKey: $viewingKey)
            }
        """)
        
        result = await self._execute_with_retry(
            mutation,
            variable_values={"viewingKey": viewing_key}
        )
        return result["connect"]

    async def disconnect_wallet(self, session_id: str) -> bool:
        """
        Disconnect a wallet using its session ID.
        
        Args:
            session_id: The session ID to disconnect
            
        Returns:
            bool: True if disconnected successfully
        """
        mutation = gql("""
            mutation($sessionId: HexEncoded!) {
                disconnect(sessionId: $sessionId)
            }
        """)
        
        await self._execute_with_retry(
            mutation,
            variable_values={"sessionId": session_id}
        )
        return True

    async def subscribe_to_blocks(self, start_height: Optional[int] = None):
        """
        Subscribe to new blocks.
        
        Args:
            start_height: Optional height to start subscription from
        """
        if not self.ws_client:
            raise SubscriptionError("WebSocket URL not provided during initialization")

        variables = {"offset": {"height": start_height}} if start_height is not None else None
        
        subscription = gql("""
            subscription($offset: BlockOffset) {
                blocks(offset: $offset) {
                    hash
                    height
                    protocolVersion
                    timestamp
                    author
                    parent {
                        hash
                        height
                    }
                    transactions {
                        hash
                        protocolVersion
                        applyStage
                        identifiers
                        raw
                        merkleTreeRoot
                    }
                }
            }
        """)

        try:
            async for result in self.ws_client.subscribe_async(subscription, variable_values=variables):
                yield self._parse_block(result["blocks"])
        except Exception as e:
            raise SubscriptionError(f"Subscription error: {str(e)}")

    async def subscribe_to_contract_actions(self, address: str, start_block_height: Optional[int] = None):
        """
        Subscribe to contract actions for a specific address.
        
        Args:
            address: The contract address to monitor
            start_block_height: Optional block height to start subscription from
        """
        if not self.ws_client:
            raise SubscriptionError("WebSocket URL not provided during initialization")

        variables = {
            "address": address,
            "offset": {"height": start_block_height} if start_block_height is not None else None
        }

        subscription = gql("""
            subscription($address: HexEncoded!, $offset: BlockOffset) {
                contractActions(address: $address, offset: $offset) {
                    address
                    state
                    chainState
                    ... on ContractCall {
                        entryPoint
                    }
                    transaction {
                        hash
                        protocolVersion
                        applyStage
                        identifiers
                        raw
                        merkleTreeRoot
                    }
                }
            }
        """)

        try:
            async for result in self.ws_client.subscribe_async(
                subscription,
                variable_values=variables
            ):
                yield self._parse_contract_action(result["contractActions"])
        except Exception as e:
            raise SubscriptionError(f"Subscription error: {str(e)}")

    async def subscribe_to_wallet(
        self,
        session_id: str,
        start_index: Optional[int] = None,
        send_progress_updates: bool = False
    ) -> WalletSyncEvent:
        """
        Subscribe to wallet events.
        
        Args:
            session_id: The wallet session ID
            start_index: Optional index to start from
            send_progress_updates: Whether to send progress updates
            
        Returns:
            WalletSyncEvent: Either a ProgressUpdate or RelevantTransaction
        """
        if not self.ws_client:
            raise SubscriptionError("WebSocket URL not provided during initialization")

        subscription = gql("""
            subscription($sessionId: HexEncoded!, $index: Int, $sendProgressUpdates: Boolean) {
                wallet(
                    sessionId: $sessionId,
                    index: $index,
                    sendProgressUpdates: $sendProgressUpdates
                ) {
                    ... on ProgressUpdate {
                        highestIndex
                        highestRelevantIndex
                        highestRelevantWalletIndex
                    }
                    ... on RelevantTransaction {
                        transaction {
                            hash
                            protocolVersion
                            applyStage
                            identifiers
                            raw
                            merkleTreeRoot
                        }
                        start
                        end
                    }
                }
            }
        """)

        try:
            async for result in self.ws_client.subscribe_async(
                subscription,
                variable_values={
                    "sessionId": session_id,
                    "index": start_index,
                    "sendProgressUpdates": send_progress_updates
                }
            ):
                wallet_event = result["wallet"]
                if "highestIndex" in wallet_event:
                    yield ProgressUpdate(
                        highest_index=wallet_event["highestIndex"],
                        highest_relevant_index=wallet_event["highestRelevantIndex"],
                        highest_relevant_wallet_index=wallet_event["highestRelevantWalletIndex"]
                    )
                else:
                    yield RelevantTransaction(
                        transaction=self._parse_transaction(wallet_event["transaction"]),
                        start=wallet_event["start"],
                        end=wallet_event["end"]
                    )
        except Exception as e:
            raise SubscriptionError(f"Subscription error: {str(e)}")

    async def _execute_with_retry(self, query, variable_values: dict = None):
        """Execute a GraphQL query with retry logic."""
        last_error = None
        
        for attempt in range(self.retry_attempts):
            try:
                return await self.http_client.execute_async(
                    query,
                    variable_values=variable_values
                )
            except Exception as e:
                last_error = e
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    
        raise GraphQLError(f"Query failed after {self.retry_attempts} attempts: {str(last_error)}")

    def _parse_block(self, data: dict) -> Block:
        """Parse block data into a Block object."""
        parent = None
        if data.get("parent"):
            parent = Block(
                hash=data["parent"]["hash"],
                height=data["parent"]["height"],
                protocol_version=0,  # Parent block has minimal info
                timestamp=0,
                author=None,
                parent=None,
                transactions=[]
            )

        return Block(
            hash=data["hash"],
            height=data["height"],
            protocol_version=data["protocolVersion"],
            timestamp=data["timestamp"],
            author=data.get("author"),
            parent=parent,
            transactions=[self._parse_transaction(tx) for tx in data["transactions"]]
        )

    def _parse_transaction(self, data: dict) -> Transaction:
        """Parse transaction data into a Transaction object."""
        block = None
        if data.get("block"):
            block = Block(
                hash=data["block"]["hash"],
                height=data["block"]["height"],
                protocol_version=0,  # Block reference has minimal info
                timestamp=0,
                author=None,
                parent=None,
                transactions=[]
            )

        return Transaction(
            hash=data["hash"],
            protocol_version=data["protocolVersion"],
            apply_stage=data["applyStage"],
            identifiers=data["identifiers"],
            raw=data["raw"],
            merkle_tree_root=data["merkleTreeRoot"],
            contract_actions=[
                self._parse_contract_action(action)
                for action in data.get("contractActions", [])
            ],
            block=block
        )

    def _parse_contract_action(self, data: dict) -> ContractAction:
        """Parse contract action data into the appropriate ContractAction object."""
        base_data = {
            "address": data["address"],
            "state": data["state"],
            "chain_state": data["chainState"],
            "transaction": self._parse_transaction(data["transaction"])
        }

        if "entryPoint" in data:
            return ContractCall(**base_data, entry_point=data["entryPoint"], deploy=None)
        elif data.get("__typename") == "ContractDeploy":
            return ContractDeploy(**base_data)
        else:
            return ContractUpdate(**base_data) 