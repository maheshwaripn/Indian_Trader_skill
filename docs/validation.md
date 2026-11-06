# Release validation — 0.1.0

Performed on 2026-11-06 in the development Linux/Python 3.12 environment:

- 25 offline unit/integration tests passed: next-open timing, gap stops, ambiguous stop/target ordering, accounting conservation, cost effects, no-trade metrics, complete ORB sessions, duplicate/out-of-order/invalid bars, row budgets, snapshot integrity, conflicting constituent events, paper duplicates/oversells/partial-sale cost basis, legacy bhavcopy conversion, HTML escaping and coach placeholder handling.
- End-to-end CLI exercised: init, doctor, demo, ingest, verify-bank, research and coach.
- Documentation relative links and portable skill headers checked.
- Independent assistant workflow exercised a partially specified RSI idea. It correctly explained the absent RSI engine rather than claiming the SMA demo tested RSI. This identified placeholder handling in the deterministic coach, which was improved and tested.
- Seeded demo: 12 trades; INR 99,656.081169 ending equity from INR 100,000, after illustrative costs. Synthetic prices only.
- Compact brief benchmark: about 82% fewer JSON payload bytes than the full demo result; this is not a measured token/cost saving. Core makes zero AI calls.

Not verified:

- Authenticated broker connections, real orders, live fills or provider entitlements.
- Yahoo network access and every optional dependency/platform combination.
- All AI products' automatic skill discovery/login flows.
- Full visual/browser QA: report generation and escaping passed, but the development browser could not launch due to environment socket restrictions. Do not treat this as a completed visual review.
- Windows/macOS matrix execution locally; a GitHub Actions matrix is provided to run these checks remotely.
- Historical alpha, out-of-sample robustness, corporate actions, authoritative PIT reconciliation or regulatory approval.

This is a research foundation. The roadmap in architecture.md remains explicit about unfinished capabilities.
