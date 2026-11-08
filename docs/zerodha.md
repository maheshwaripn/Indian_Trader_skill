# Zerodha / Kite setup

Reviewed on 2026-11-06. Documentation only in the current release; no live or authenticated integration test was performed.

## 1. Account and developer application

1. Use your own Zerodha trading account with the required authentication setup.
2. Read https://kite.trade/docs/connect/v3/ and create the appropriate Kite Connect developer application through the official interface.
3. Register the redirect URL exactly as required. Keep API secret server-side; never expose it in dashboard JavaScript.
4. Complete the documented user login/request-token exchange. Respect token expiry and supported reauthentication; do not bypass interactive security requirements.
5. Store credentials privately. Suggested future-adapter variables are `KITE_API_KEY`, `KITE_API_SECRET`, `KITE_ACCESS_TOKEN`; v0.1 does not consume them.
6. Confirm your app's market-data entitlement and charges from the broker before subscribing.

## 2. Historical and live data

Download and version the instrument master. Map instrument tokens, exchange, segment and symbol; do not assume a broker token is a permanent economic identifier. Fetch a small historical sample, normalise to the canonical schema, validate, and ingest. Check gaps and corporate-action conventions. Use the documented WebSocket workflow only if live data is necessary.

The repository's paper ledger is independent of Zerodha. A paper fill entered by a user does not prove that a live broker order would fill at that price.

## 3. Static IP registration

Use the dedicated official guide:
https://support.zerodha.com/category/trading-and-markets/general-kite/kite-api/articles/static-ip

At review time this guide states static IP is required for API-based order placement from 1 April 2026, while the listed market-data and other APIs can be accessed from other IPs. A separate FAQ showed a conflicting year during review; use the dedicated guide and confirm current requirements with the broker rather than propagate the discrepancy.

1. Obtain and verify a fixed public egress IP for your execution host.
2. Sign in to the Kite Connect developer account and open the static-IP configuration in its profile/settings area.
3. Register permitted primary and, where supported, secondary IPs following current broker rules.
4. Verify registration and account scope. Check restrictions on changing IPs and sharing them before planning failover.
5. Keep the execution worker on the registered network path. Do not rely on a roaming laptop's dynamic address.
6. Test read-only connectivity and account reconciliation before any separately approved live pilot.

## 4. Future execution adapter

Official order lifecycle documentation: https://kite.trade/docs/connect/v3/orders/.

A successful order submission is not proof of a fill. Poll/consume order updates, reconcile trades and positions, track rejected and partially filled orders, and distinguish broker order ID from local intent ID. Never retry an uncertain submission blindly. Check applicable order-type and product restrictions at implementation time.

Zerodha follows Dhan in the execution roadmap. Refer to [live readiness](live-readiness.md); no CLI command in this release sends a broker order.
