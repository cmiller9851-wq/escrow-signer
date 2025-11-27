# Escrow Signer — Production-Ready Ethereum Fund Releaser

Securely releases the full balance from an escrow contract.  
Mainnet triple-guarded, dry-run mode, retries, Slack + Telegram alerts.

## Test (Sepolia — always start here)
```bash
docker run --rm \
  -e RPC_URL="https://sepolia.infura.io/v3/YOUR_ID" \
  -e PRIVATE_KEY="your_test_key" \
  -e ESCROW_CONTRACT="0x..." \
  -e RECIPIENT="0x..." \
  -e DRY_RUN=true \
  ghcr.io/cmiller9851-wq/escrow-signer:latest
docker run --rm \
  -e RPC_URL="https://mainnet.infura.io/v3/..." \
  -e PRIVATE_KEY="..." \
  -e ESCROW_CONTRACT="0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f" \
  -e RECIPIENT="0x742d35Cc6634C0532925a3b844Bc454e4438f44e" \
  -e I_ACKNOWLEDGE_MAINNET=true \
  ghcr.io/cmiller9851-wq/escrow-signer:latest
