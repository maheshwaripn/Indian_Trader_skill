# Dhan setup: data first, live routing later

Reviewed against official sources on 2026-11-06. This is an implementation guide, not a claim that this repository has an executable Dhan adapter. No account connection or live trade was tested for v0.1.

## 1. Prepare the account and environment

1. Use your own active Dhan account and complete the broker's required account/segment setup.
2. Read https://dhanhq.co/docs/v2/ and its current authentication, historical-data and release pages.
3. In Dhan Web, open the broker's DhanHQ API access area. Confirm separately which trading and market-data services you are entitled to; don't assume data is free because trading APIs are available.
4. Create the credentials through the official interface. Follow the broker's current token expiry and renewal process.
5. Store credentials locally using restricted environment variables or a secret manager. Never commit them, paste them into AI prompts, or print them in diagnostic logs.
6. On Linux, restrict any credential file to the service user with mode 600. Do not source untrusted files as shell code.

Suggested variable names for a future adapter: `DHAN_CLIENT_ID`, `DHAN_ACCESS_TOKEN`. These names are project conventions, not automatic configuration in v0.1.

## 2. Data connection sequence

1. Fetch the current official instrument master with a future/read-only adapter or your own validated client.
2. Map exchange segment and broker security ID to a stable research identifier. Store the master version.
3. Request a small historical period using the official documented endpoint and entitlement.
4. Convert to canonical OHLCV with timezone, bar-open timestamp and adjustment policy documented.
5. Validate and ingest using the existing CLI.
6. Test pagination, rate limiting, token expiry, missing bars and duplicate overlap before scheduling downloads.
7. Add live quotes only when required; do not mix quotes with completed bars without a documented aggregator.

If the response is empty, inspect entitlement, date range and instrument ID. Do not fill absent prices with zero or silently remove the instrument from historical research.

## 3. Paper trading

Use the internal ledger with user-supplied simulated fills. It is not connected to Dhan and does not imply Dhan supplies a sandbox. Record fill assumptions, fee model and data source. Reconcile cash and shares after every exercise.

## 4. Static IP and eventual live use

Official sources:

- https://dhanhq.co/docs/v2/authentication/
- https://dhanhq.co/docs/v2/orders/
- https://dhanhq.co/docs/v2/releases/

Dhan's documentation requires static-IP whitelisting for order APIs, including placing, modifying and cancelling orders. The authentication guide describes primary/secondary IP registration and a seven-day change restriction (or exchange-directed requirement). Recheck before changes.

1. Obtain a fixed public outbound IP from your ISP or VPS provider. Verify actual egress; a server's displayed interface IP can differ behind NAT.
2. Confirm the account/IP-use restrictions with Dhan. Do not share an execution IP indiscriminately across unrelated clients.
3. Register the IP through Dhan Web or the documented IP API; retain the confirmation privately.
4. Ensure backups/failover use a registered permitted IP before relying on them.
5. Verify authentication and read-only endpoints first.
6. Complete [live readiness](live-readiness.md) before adding an order adapter.
7. Any future real-order connectivity test needs explicit user authorisation and a concrete order ticket. An installer must never submit a “test” real order automatically.

## Adapter acceptance requirements

Dhan is the first planned execution adapter. It must support unique intent IDs, timeout reconciliation before retries, partial fills, rejected orders, cancel/modify acknowledgement, current positions/funds, credential expiry, loss limits, manual override and durable audit logs. Broker-side exits must be verified; an AI conversation is not a reliable protective-stop service.
