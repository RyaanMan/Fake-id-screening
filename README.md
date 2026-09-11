# AI-Based Fake Identity & Document Screening System — starter

This starter adds a role-based Streamlit UI, FastAPI service, SQLite reference/audit database, SHA-256 document fingerprinting, ELA, metadata, SIFT copy-move signal, and a local Ethereum-compatible DocumentRegistry prototype.

## Roles in the prototype
- Immigration / Check Post Officer: run a screening and see document evidence, reference status, blockchain result and recommended action.
- Supervisor: review medium/high-risk cases and audit history.
- Auditor: read-only audit log.
- System Administrator: prototype health/configuration view.

The role switch is a UI demonstration, not real authentication. Production should use institutional IAM/SSO and least-privilege authorization.

## Government integration disclaimer
This prototype does not connect to live Ministry of Home Affairs / Bureau of Immigration systems or government databases. The reference records are simulated for hackathon demonstration.

## Blockchain privacy
Do not place passport images, names, DOBs, addresses, raw OCR, or face data on-chain. The prototype is designed to store a SHA-256 fingerprint plus limited issuer/status metadata on-chain.
