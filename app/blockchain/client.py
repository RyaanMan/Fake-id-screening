from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from web3 import Web3
from web3.exceptions import ContractLogicError


BASE_DIR = Path(__file__).resolve().parents[2]
DEPLOYMENT_FILE = BASE_DIR / "blockchain" / "deployment.json"


class BlockchainClient:
    def __init__(
        self,
        rpc_url: str | None = None,
        private_key: str | None = None,
    ) -> None:
        self.rpc_url = rpc_url or os.getenv("BLOCKCHAIN_RPC_URL", "http://127.0.0.1:8545")
        self.private_key = private_key or os.getenv("BLOCKCHAIN_PRIVATE_KEY")
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))

        if not self.w3.is_connected():
            raise ConnectionError(f"Cannot connect to blockchain RPC: {self.rpc_url}")

        if not DEPLOYMENT_FILE.exists():
            raise FileNotFoundError(
                f"Missing {DEPLOYMENT_FILE}. Deploy DocumentRegistry first."
            )

        deployment = json.loads(DEPLOYMENT_FILE.read_text())
        self.contract_address = Web3.to_checksum_address(deployment["address"])
        self.contract = self.w3.eth.contract(
            address=self.contract_address,
            abi=deployment["abi"],
        )

        if self.private_key:
            self.account = self.w3.eth.account.from_key(self.private_key)
        else:
            self.account = None

    def status(self) -> dict[str, Any]:
        return {
            "connected": self.w3.is_connected(),
            "chain_id": self.w3.eth.chain_id,
            "block_number": self.w3.eth.block_number,
            "contract_address": self.contract_address,
            "account": self.account.address if self.account else None,
        }

    def verify_document(self, document_hash_hex: str) -> dict[str, Any]:
        document_hash = bytes.fromhex(document_hash_hex)
        record = self.contract.functions.getDocument(document_hash).call()
        # Solidity tuple order: issuer, issuedAt, expiry, active, exists.
        issuer, issued_at, expiry, active, exists = record
        return {
            "exists": bool(exists),
            "issuer": issuer,
            "issued_at": int(issued_at),
            "expiry": int(expiry),
            "active": bool(active),
            "match": bool(exists and active),
        }

    def register_document(
        self,
        document_hash_hex: str,
        issuer: str,
        expiry: int,
    ) -> str:
        if not self.account:
            raise RuntimeError("BLOCKCHAIN_PRIVATE_KEY is required for registration")

        document_hash = bytes.fromhex(document_hash_hex)
        nonce = self.w3.eth.get_transaction_count(self.account.address)
        tx = self.contract.functions.registerDocument(
            document_hash,
            issuer,
            expiry,
        ).build_transaction(
            {
                "from": self.account.address,
                "nonce": nonce,
                "chainId": self.w3.eth.chain_id,
                "gas": 400_000,
                "gasPrice": self.w3.eth.gas_price,
            }
        )
        signed = self.w3.eth.account.sign_transaction(tx, self.private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        return receipt.transactionHash.hex()

    def revoke_document(self, document_hash_hex: str) -> str:
        if not self.account:
            raise RuntimeError("BLOCKCHAIN_PRIVATE_KEY is required for revocation")

        document_hash = bytes.fromhex(document_hash_hex)
        nonce = self.w3.eth.get_transaction_count(self.account.address)
        tx = self.contract.functions.revokeDocument(document_hash).build_transaction(
            {
                "from": self.account.address,
                "nonce": nonce,
                "chainId": self.w3.eth.chain_id,
                "gas": 200_000,
                "gasPrice": self.w3.eth.gas_price,
            }
        )
        signed = self.w3.eth.account.sign_transaction(tx, self.private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        return receipt.transactionHash.hex()
