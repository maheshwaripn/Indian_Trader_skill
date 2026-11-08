# Release validation — 0.2.0

Performed on 2026-11-08 on Linux, Python 3.12, with and without PyArrow:

- 49 offline tests pass (29 from 0.1 plus 20 new): hand-computed futures round-trip charges (₹499.64 for 500 x ₹1,600 on 4 May 2026), STT change dates, delivery-free broker and DP charge, Indian costs reducing results, calendar classification and missing-session detection, split-like gaps blocked unless allowed, ORB skipping an incomplete day while trading a complete one, futures whole lots and one-lot rejection, membership blocking entries, windows excluding earlier entries, R sign matching P&L, reproducible random entries, evaluate and sweep end to end, neighbour sets, a moved workspace bank verifying (new and v0.1 catalogues), UDiFF conversion, membership lookup, v0.1 paper ledger migration to paise, estimated fees and marking.
- UDiFF converter run on real NSE CM bhavcopies for 4 and 5 November 2026: 5,481 EQ rows, RELIANCE 4 Nov close 1,311.00.
- Opening-range strategy with one bar removed from one of five days: v0.1 rejected the whole file; 0.2 skips that day and trades the rest.
- Seeded demo: 12 trades; INR 99,134.199916 ending equity from INR 100,000 after Indian delivery charges and ₹20 per order. Synthetic prices only.
- Reading 300,000 rows with PyArrow installed: 7.6 s and about 430 MB of memory on this machine, mostly row validation. Plan on roughly 1.4 KB of memory a row for the `lab` and `vps` budgets.
- `ruff check` with the project configuration is clean.

Not verified:

- Authenticated broker connections, real orders, live fills or provider entitlements.
- Cost rates before 2023 and broker presets against every broker's current card; check contract notes.
- Yahoo network access and every optional dependency/platform combination.
- Windows/macOS locally; the GitHub Actions matrix runs these remotely.
- Historical alpha, adjusted prices, authoritative PIT reconciliation or regulatory approval.

## Independent follow-up review

The original 49 tests passed before changes. Added regressions cover overlapping development/validation/final windows, unsupported fee dates, zero/invalid order values, incomplete paper valuations, sub-paise fills, forward ledger schema refusal, exchange-local calendar dates and invalid resampling budgets. Missing marks now produce `equity: null` and a separate known-value subtotal, never a misleading partial equity total. Fee estimates reject dates outside explicit coverage. Paper marks may use a session date or an offset-aware timestamp.

Shared modules now live in `indian_market_core`. Official Budget and Muhurat circulars were read; the daily calendar notes the separate CAS close. No broker, live-order or real-strategy verification was performed in this follow-up.
