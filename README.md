# Escrow Signer — Production Ready

Releases full escrow balance with triple-checked mainnet protection.

### Run (test on Sepolia first)
```bash
docker run --rm -e RPC_URL=... -e PRIVATE_KEY=... -e ESCROW_CONTRACT=... -e RECIPIENT=... ghcr.io/yourname/escrow-signer:latest
