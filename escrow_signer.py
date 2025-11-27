#!/usr/bin/env python3
"""
Production-ready escrow fund releaser — mainnet guarded, dry-run, retries, Slack/Telegram alerts
"""
from web3 import Web3
from eth_account import Account
import os
import sys
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

# ─── Config from env only ─────────────────────────────────────
RPC_URL = os.getenv("RPC_URL")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")                   # no 0x prefix in env
ESCROW_CONTRACT = os.getenv("ESCROW_CONTRACT")
RECIPIENT = os.getenv("RECIPIENT")
CHAIN_ID = int(os.getenv("CHAIN_ID", "1"))
GAS_PRICE_GWEI = int(os.getenv("GAS_PRICE_GWEI", "7"))
GAS_LIMIT = int(os.getenv("GAS_LIMIT", "200000"))
DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"
I_ACKNOWLEDGE_MAINNET = os.getenv("I_ACKNOWLEDGE_MAINNET", "false").lower() == "true"

SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK_URL")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT = os.getenv("TELEGRAM_CHAT_ID")

# Minimal ABI — only releaseFunds
ABI = [{"inputs":[{"name":"_recipient","type":"address"},{"name":"_amount","type":"uint256"}],"name":"releaseFunds","outputs":[],"stateMutability":"nonpayable","type":"function"}]

# ─── Inline Notifications (no separate files needed) ──────────
def notify(msg: str):
    if SLACK_WEBHOOK:
        try: requests.post(SLACK_WEBHOOK, json={"text": msg}, timeout=10)
        except: pass
    if TELEGRAM_TOKEN and TELEGRAM_CHAT:
        try:
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                          data={"chat_id": TELEGRAM_CHAT, "text": msg, "disable_web_page_preview": True}, timeout=10)
        except: pass

# ─── Resilient broadcast ───────────────────────────────────────
@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=2, max=60))
def send_tx(w3, signed):
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    return w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)

# ─── Main ─────────────────────────────────────────────────────
def main():
    missing = [v for v in ["RPC_URL","PRIVATE_KEY","ESCROW_CONTRACT","RECIPIENT"] if not os.getenv(v)]
    if missing:
        print("Missing required env vars:", missing); sys.exit(1)

    if CHAIN_ID == 1 and not I_ACKNOWLEDGE_MAINNET:
        print("MAINNET blocked — set I_ACKNOWLEDGE_MAINNET=true")
        notify("Escrow signer blocked by mainnet guard")
        sys.exit(1)

    w3 = Web3(Web3.HTTPProvider(RPC_URL, request_kwargs={"timeout": 60}))
    if not w3.is_connected():
        notify("Failed to connect to RPC")
        sys.exit(1)

    pk = PRIVATE_KEY if PRIVATE_KEY.startswith("0x") else "0x" + PRIVATE_KEY
    account = Account.from_key(pk)
    contract = w3.eth.contract(address=Web3.to_checksum_address(ESCROW_CONTRACT), abi=ABI)

    amount_wei = w3.eth.get_balance(ESCROW_CONTRACT)
    amount_eth = w3.from_wei(amount_wei, "ether")
    print(f"Releasing {amount_eth} ETH → {RECIPIENT}")

    if DRY_RUN:
        notify(f"DRY RUN: Would release {amount_eth} ETH from {ESCROW_CONTRACT}")
        print("DRY RUN — no transaction sent")
        return

    tx = contract.functions.releaseFunds(Web3.to_checksum_address(RECIPIENT), amount_wei).build_transaction({
        "chainId": CHAIN_ID,
        "nonce": w3.eth.get_transaction_count(account.address),
        "gas": GAS_LIMIT,
        "gasPrice": w3.to_wei(GAS_PRICE_GWEI, "gwei"),
    })

    signed = w3.eth.account.sign_transaction(tx, pk)
    receipt = send_tx(w3, signed)

    explorer = "" if CHAIN_ID != 1 else ""
    url = f"https://{explorer}etherscan.io/tx/{receipt.transactionHash.hex()}"

    if receipt.status == 1:
        notify(f"ESCROW RELEASED\n{amount_eth} ETH → {RECIPIENT}\n{url}")
        print("SUCCESS")
    else:
        notify(f"ESCROW RELEASE REVERTED\n{url}")
        print("REVERTED")
    print(url)

if __name__ == "__main__":
    main()
