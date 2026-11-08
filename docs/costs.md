# Trading costs in India

`research`, `evaluate`, `sweep`, `cost-calc` and `paper-fill --auto-fee` share one dated cost model (`src/indian_trader/costs.py`). It is an estimate for research. Check your broker's contract note and the exchange's current schedule before relying on a number.

## What is charged

| Item | Delivery | Intraday | Futures | Options (on premium) |
|---|---|---|---|---|
| STT | 0.1% buy and sell | 0.025% sell | sell: 0.01%, 0.0125% from 2023-04-01, 0.02% from 2024-10-01, 0.05% from 2026-04-01 | sell: 0.05%, 0.0625% from 2023-04-01, 0.1% from 2024-10-01, 0.15% from 2026-04-01 |
| NSE transaction charge | 0.00325%, 0.00297% from 2024-10-01 | same as delivery | 0.0019%, 0.00173% from 2024-10-01 | 0.053%, 0.03503% from 2024-10-01 |
| Stamp duty (buy) | 0.015% | 0.003% | 0.002% | 0.003% |
| SEBI fee | 0.0001% (₹10 a crore) on both sides | | | |
| IPFT | 0.0001% (options 0.0005%) | | | |
| GST | 18% on brokerage, exchange charge, SEBI fee and IPFT | | | |

Brokerage and depository (DP) charges depend on the broker. Presets:

| Preset | Brokerage per order | Delivery | DP charge per delivery sale |
|---|---|---|---|
| `flat20` (default) | ₹20 | ₹20 | none |
| `discount` | lower of 0.03% and ₹20 | free | ₹13.50 plus GST |
| `zero` | none | free | none |

Earlier history is approximate: the tool applies the first listed rate before the first change date. Sources: NSE circulars and rate pages, the Finance Acts 2023 and 2026 for STT, and broker rate cards. The values were last reviewed on 2026-11-08.

## Examples

```bash
indian-trader cost-calc --product futures --qty 500 --buy-price 1600 --sell-price 1600 --buy-date 2026-05-04
indian-trader cost-calc --product options --qty 65 --buy-price 100 --sell-price 110 --buy-date 2026-05-04
```

The first comes to about ₹500 for ₹8 lakh of futures bought and sold: STT ₹400, exchange ₹27.68, brokerage ₹40, GST ₹12.76, stamp ₹16, SEBI and IPFT ₹3.20. The second comes to about ₹64 for one Nifty lot.

## In back-tests

`--costs india` is the default and picks the product from the strategy (trend: delivery, ORB: intraday) unless `--product` is given. `--costs bps --fee-bps N` keeps the v0.1 flat fee. `--cost-stress K` multiplies slippage and brokerage by K and leaves statutory rates unchanged. `evaluate` reports 1x, 2x and 3x. Planned risk per trade includes estimated costs, and each trade's result is also shown in R.
