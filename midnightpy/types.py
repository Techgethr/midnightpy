from dataclasses import dataclass
from typing import List, Optional, Union
from datetime import datetime

@dataclass
class Block:
    hash: str
    height: int
    protocol_version: int
    timestamp: int
    author: Optional[str]
    parent: Optional['Block']
    transactions: List['Transaction']

    @property
    def datetime(self) -> datetime:
        return datetime.fromtimestamp(self.timestamp)

@dataclass
class Transaction:
    hash: str
    protocol_version: int
    apply_stage: str
    identifiers: List[str]
    raw: str
    merkle_tree_root: str
    contract_actions: List['ContractAction']
    block: Optional[Block] = None

@dataclass
class ContractAction:
    address: str
    state: str
    chain_state: str
    transaction: Transaction

@dataclass
class ContractCall(ContractAction):
    entry_point: str
    deploy: 'ContractDeploy'

@dataclass
class ContractDeploy(ContractAction):
    pass

@dataclass
class ContractUpdate(ContractAction):
    pass

@dataclass
class MerkleTreeCollapsedUpdate:
    protocol_version: int
    start: int
    end: int
    update: str

@dataclass
class ProgressUpdate:
    highest_index: int
    highest_relevant_index: int
    highest_relevant_wallet_index: int

@dataclass
class RelevantTransaction:
    transaction: Transaction
    start: int
    end: int

WalletSyncEvent = Union[ProgressUpdate, RelevantTransaction] 