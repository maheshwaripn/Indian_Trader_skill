# Live readiness and dated regulatory references

**The current release (0.2) does not place real orders.** This guide prepares a future separately tested adapter. An educational disclaimer does not waive legal duties, broker terms or responsibility for losses. This is an engineering checklist, not a legal certification.

## Official source register

Reviewed 2026-11-06; recheck before deployment and after broker/exchange changes.

| Topic | Official source | How to use it |
|---|---|---|
| Retail algo framework | https://www.sebi.gov.in/legal/circulars/feb-2025/safer-participation-of-retail-investors-in-algorithmic-trading_91614.html | Identify obligations by activity and role |
| Implementation timeline | https://www.sebi.gov.in/sebi_data/attachdocs/sep-2025/1759232056254.pdf | States applicability to all stock brokers from 1 April 2026 |
| NSE algorithmic trading | https://www.nseindia.com/ | Locate current retail-algo circulars, implementation standards and operational modalities |
| Dhan authentication/IP | https://dhanhq.co/docs/v2/authentication/ | Account-specific authentication and IP procedures |
| Dhan orders | https://dhanhq.co/docs/v2/orders/ | Order lifecycle and static-IP requirements |
| Zerodha IP | https://support.zerodha.com/category/trading-and-markets/general-kite/kite-api/articles/static-ip | Current developer-account IP setup |
| Kite API | https://kite.trade/docs/connect/v3/ | Authentication, instruments and order lifecycle |

Do not treat this source list as exhaustive current clearance. Exchange circulars issued after the baseline may modify obligations. Record the exact circular IDs, effective dates and broker confirmation for the proposed use. Escalate unresolved interpretation to the broker/compliance professional.

## Establish the operating role

Distinguish personal self-developed strategies, third-party algo providers, commercial strategy distribution, advice/research services, and handling other people's accounts. Registration, exchange approvals, tagging, hosting, rate limits and other requirements may differ. Publishing open-source code does not automatically authorise every commercial deployment of it.

Before activation, obtain broker confirmation for:

- Whether the proposed API/algo arrangement is permitted for this account and use case.
- Applicable registration/tagging and order-rate requirements; do not hard-code a remembered threshold.
- Supported order types/products and applicable margin/segment restrictions.
- Static IP, authentication, session and audit-log requirements.
- Any restrictions on third-party hosting, provider distribution or shared network infrastructure.

## Static-IP implementation steps

1. Decide where the execution worker runs. Research can run elsewhere.
2. Obtain fixed outbound public IP from the ISP/VPS provider. Account for NAT, IPv4/IPv6 and failover routes.
3. Verify egress using a trusted service from that worker, without exposing credentials.
4. Register through the broker's official process and retain confirmation.
5. Restrict inbound access with firewall and SSH keys; IP registration does not secure the VPS itself.
6. Check that a secondary host uses its own permitted registered route.
7. Recheck egress before sessions and after network changes. A mismatch stops new orders.
8. Keep access to the broker's own application for manual intervention.

## Promotion gates

| Stage | Evidence required |
|---|---|
| Research | Data lineage, explicit rules, costs and bias disclosures |
| Paper | Reproducible signals, simulated fill assumptions and accounting checks |
| Execution simulation | Rejects, gaps, timeouts, partial fills and duplicate prevention tested |
| Pilot candidate | Broker/current-requirement confirmation, fixed egress, reconciled balances, alerts and operator runbook |
| User-authorised pilot | Explicit risk settings, concrete activation decision, small intended scope and monitored operation |

Passing a stage does not prove profitability. Capital size and risk choices belong to the user within applicable rules. Loss/drawdown thresholds may stop **new entries**; protective exits need a separate policy so a loss lock does not accidentally prevent risk reduction.

## Non-negotiable correctness properties for a future adapter

- Bind approval to exact symbol, side, quantity, prices, account, strategy/config version and expiry.
- Revalidate market data, positions, cash/margin and limits immediately before submission.
- Persist intent before network calls. Reconcile uncertain outcomes before retrying.
- Keep order, fill, position and cash states distinct.
- Handle partial fills, rejected stops, disconnections, token expiry, market halts and price bands.
- Provide manual override, kill-switch and durable logs. Document what the kill-switch cancels and what it cannot close.
- Confirm broker-supported protective orders; do not assume an assistant will remain online.
- Separate paper and live credentials, databases and process permissions.

Do not claim “SEBI approved”, “institutional grade” or “production ready” without evidence of the specific approval and validation being asserted.
