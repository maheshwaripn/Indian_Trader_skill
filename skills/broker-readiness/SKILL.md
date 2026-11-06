---
name: indian-trader-broker-readiness
description: Guide Dhan or Zerodha data and eventual live-trading setup, static-IP configuration, account permissions, paper validation and current compliance checks.
---

Read `docs/live-readiness.md` and the chosen broker guide. State immediately that v0.1 has no live-order adapter.

1. Establish personal research versus live execution versus third-party service intent. Do not assume one regulatory pathway covers all roles.
2. Verify current official broker/exchange/SEBI requirements before giving time-sensitive instructions. Separate verified requirements from interpretation and unresolved questions.
3. Guide account creation, developer app, permissions and authentication through official interfaces. Never ask the user to paste passwords, secrets or OTPs into chat.
4. For data, test read-only access, instrument mapping, coverage and rate limits before scheduling. Explain subscription/entitlement differences without inventing prices.
5. For future execution, identify actual fixed public egress, broker registration, failover implications and change restrictions. Do not change IP registration without user authorisation.
6. Require tested order intent, fills, reconciliation, duplicate prevention, emergency procedures and current broker permission before considering a live pilot.
7. Explain user-adjustable risk preferences and boundaries. Never bypass platform permissions, broker restrictions or law.

An educational notice is not legal clearance. Do not claim setup or live testing occurred when only instructions were provided. No installer or connectivity test may submit a real order implicitly.
