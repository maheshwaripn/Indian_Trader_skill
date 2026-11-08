"""v0.2: costs, calendar, corporate-action checks, sessions, lots, membership, windows, nulls, sweeps, bank portability, UDiFF and paper paise."""
import csv
import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from indian_trader import bank, calendar, costs, paper, research, universe, validation
from indian_trader.cli import demo
from indian_trader.core import read_bars, suspect_jumps
from indian_trader.providers import bhavcopy, save

IST = timezone(timedelta(hours=5, minutes=30))


def daily(closes, symbol="TEST", start=datetime(2024, 1, 1, 9, 15, tzinfo=IST), opens=None):
    return [dict(timestamp=(start + timedelta(days=i)).isoformat(), symbol=symbol, open=(opens[i] if opens else c), high=max(c, opens[i] if opens else c),
                 low=min(c, opens[i] if opens else c), close=c, volume=1000) for i, c in enumerate(closes)]


def session(day, prices, symbol="ORB", drop=None):
    start = datetime(day.year, day.month, day.day, 9, 15, tzinfo=IST); out = []
    for i in range(75):
        if drop is not None and i == drop:
            continue
        p = prices(i); out.append(dict(timestamp=(start + timedelta(minutes=5 * i)).isoformat(), symbol=symbol, open=p, high=p + .1, low=p - .1, close=p, volume=1000))
    return out


class Costs(unittest.TestCase):
    def test_futures_round_trip_by_hand(self):
        # 500 x 1600 bought and sold on 4 May 2026: STT 0.05% of 8,00,000 = 400; exchange 0.00173% of 16,00,000 = 27.68;
        # SEBI 1.60; IPFT 1.60; stamp 0.002% of 8,00,000 = 16; brokerage 2 x 20 = 40; GST 18% of (40 + 27.68 + 1.60 + 1.60) = 12.7584
        self.assertAlmostEqual(costs.round_trip("futures", "2026-05-04", "2026-05-04", 500, 1600, 1600)["total"], 499.6384, places=4)

    def test_stt_dates(self):
        self.assertEqual(costs.rates("futures", "2026-03-31")["stt_sell"], 0.0002)
        self.assertEqual(costs.rates("futures", "2026-04-01")["stt_sell"], 0.0005)
        self.assertEqual(costs.rates("options", "2024-09-30")["stt_sell"], 0.000625)
        self.assertEqual(costs.rates("options", "2026-04-01")["stt_sell"], 0.0015)

    def test_delivery_free_broker_and_dp(self):
        free = costs.leg("delivery", "2026-05-04", "buy", 100000, "discount")
        self.assertEqual(free["brokerage"], 0)
        self.assertGreater(costs.leg("delivery", "2026-05-04", "sell", 100000, "discount")["dp"], 0)

    def test_india_costs_exceed_zero_cost_run(self):
        b = daily([10, 9, 11, 12, 13, 14])
        zero = research.run(b, lookback=2, costs="bps", fee_bps=0, slippage_bps=0)
        india = research.run(b, lookback=2, slippage_bps=0)
        self.assertLess(india["metrics"]["net_pnl"], zero["metrics"]["net_pnl"])
        self.assertEqual(india["parameters"]["costs"], "india")


class Calendar(unittest.TestCase):
    def test_classify(self):
        cal = calendar.load()
        self.assertEqual(calendar.classify(cal, "2026-01-26"), "CLOSED")
        self.assertEqual(calendar.classify(cal, "2026-11-08"), "SPECIAL_SESSION")
        self.assertEqual(calendar.classify(cal, "2026-02-01"), "TRADING_DAY")
        self.assertEqual(calendar.classify(cal, "2025-01-01"), "UNKNOWN")

    def test_missing_session_found(self):
        b = daily([10, 11, 12, 13], start=datetime(2026, 11, 2, 9, 15, tzinfo=IST))   # Mon..Thu
        del b[1]
        r = calendar.check(read_bars_list(b), calendar.load())
        self.assertEqual(r["symbols"]["TEST"]["missing_sessions"], ["2026-11-03"])


def read_bars_list(rows):
    d = tempfile.mkdtemp(); p = Path(d) / "b.csv"; save(rows, p); return read_bars(p)


class Engine(unittest.TestCase):
    def test_split_like_gap_blocks_unless_allowed(self):
        b = daily([100, 100, 100, 50, 50], opens=[100, 100, 100, 50, 50])
        self.assertEqual(len(suspect_jumps(b)), 1)
        with self.assertRaisesRegex(ValueError, "split"):
            research.run(b, lookback=2)
        research.run(b, lookback=2, allow_suspect_jumps=True)

    def test_orb_skips_incomplete_day_and_trades_complete_one(self):
        day1, day2 = datetime(2024, 1, 2), datetime(2024, 1, 3)
        rows = session(day1, lambda i: 100 if i < 3 else 101, drop=40) + session(day2, lambda i: 100 if i < 3 else 101)
        r = research.run(rows, strategy="orb", stop_pct=10, target_r=10, costs="bps", fee_bps=0, slippage_bps=0)
        self.assertEqual(r["skipped_sessions"], {"ORB": ["2024-01-02"]})
        self.assertEqual(len(r["trades"]), 1)
        self.assertTrue(r["trades"][0]["entry_time"].startswith("2024-01-03"))
        self.assertEqual(r["trades"][0]["reason"], "session_close_proxy")

    def test_futures_whole_lots_and_rejection(self):
        b = daily([10, 9, 11, 12, 13, 14])
        lots = {"TEST": [("2020-01-01", 50)]}
        r = research.run(b, lookback=2, product="futures", lots=lots, risk_pct=5, costs="bps", fee_bps=0, slippage_bps=0)
        self.assertTrue(r["trades"] and all(t["qty"] % 50 == 0 for t in r["trades"]))
        big = research.run(b, lookback=2, product="futures", lots={"TEST": [("2020-01-01", 100000)]}, costs="bps", fee_bps=0, slippage_bps=0)
        self.assertEqual(big["metrics"]["trades"], 0)
        self.assertGreater(big["rejections"]["one_lot_exceeds_risk_budget"], 0)

    def test_membership_blocks_entries(self):
        b = daily([10, 9, 11, 12, 13, 14])
        r = research.run(b, lookback=2, member=lambda s, d: False, costs="bps", fee_bps=0, slippage_bps=0)
        self.assertEqual(r["metrics"]["trades"], 0)

    def test_window_excludes_earlier_entries(self):
        b = daily([10, 9, 11, 12, 13, 14, 15, 16])
        r = research.run(b, lookback=2, start="2024-01-06", costs="bps", fee_bps=0, slippage_bps=0)
        self.assertTrue(all(t["entry_time"][:10] >= "2024-01-06" for t in r["trades"]))
        self.assertTrue(r["equity"][0]["timestamp"][:10] >= "2024-01-06")

    def test_r_multiple_matches_sign(self):
        demo_path = demo(Path(tempfile.mkdtemp()) / "d.csv")
        r = research.run(read_bars(demo_path))
        self.assertTrue(r["trades"])
        for t in r["trades"]:
            self.assertEqual(t["net_pnl"] > 0, t["r_multiple"] > 0)

    def test_random_entries_reproducible(self):
        bars = read_bars(demo(Path(tempfile.mkdtemp()) / "d.csv"))
        a = research.run(bars, entry="random", seed=5, entry_rate=0.1)
        b = research.run(bars, entry="random", seed=5, entry_rate=0.1)
        self.assertEqual(a["metrics"], b["metrics"])


class Validation(unittest.TestCase):
    def test_evaluate_and_sweep_on_demo(self):
        bars = read_bars(demo(Path(tempfile.mkdtemp()) / "d.csv"))
        e = validation.evaluate(bars, {"lookback": 10}, ("2024-01-01", "2024-03-31"), ("2024-04-01", "2024-06-30"), seeds=5)
        self.assertIn(e["verdict"], ("DOES_NOT_PASS", "PASSES_PREDECLARED_CHECKS_NOT_PROOF"))
        self.assertEqual(set(e["results"]), {"development", "validation"})
        s = validation.sweep(bars, {}, {"lookback": [5, 10, 20]}, ("2024-01-01", "2024-06-30"), min_trades=1, flips=50)
        self.assertEqual(s["settings_tried"], 3)
        self.assertTrue(0 <= s["reality_check"]["p_value"] <= 1)

    def test_neighbours(self):
        self.assertEqual(sorted(validation.neighbours((10, 2), {"a": [5, 10, 20], "b": [1, 2]})), [(5, 2), (10, 1), (20, 2)])


class Storage(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.p = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_bank_survives_moving_workspace(self):
        src = demo(self.p / "d.csv"); root = self.p / "ws" / "bank"
        bank.ingest(root, "demo", src, "synthetic", 1000, "raw")
        moved = self.p / "moved"; (self.p / "ws").rename(moved)
        self.assertTrue(bank.verify(moved / "bank")[0]["ok"])
        self.assertEqual(bank.catalogue(moved / "bank")[0]["adjustment"], "raw")

    def test_v01_absolute_catalogue_still_verifies_after_move(self):
        src = demo(self.p / "d.csv"); root = self.p / "ws" / "bank"
        r = bank.ingest(root, "demo", src, "synthetic", 1000)
        with sqlite3.connect(root / "catalogue.sqlite") as c:
            c.execute("UPDATE datasets SET path=?", (str(Path(r["path"]).resolve()),))
        c.close()
        (self.p / "ws").rename(self.p / "moved")
        self.assertTrue(bank.verify(self.p / "moved" / "bank")[0]["ok"])

    def test_udiff_conversion_keeps_eq_stock_rows(self):
        p = self.p / "u.csv"
        p.write_text("TradDt,BizDt,Sgmt,Src,FinInstrmTp,FinInstrmId,ISIN,TckrSymb,SctySrs,OpnPric,HghPric,LwPric,ClsPric,TtlTradgVol\n"
                     "2026-11-04,2026-11-04,CM,NSE,STK,1,X,RELIANCE,EQ,1301.9,1318.9,1296,1311,19451679\n"
                     "2026-11-04,2026-11-04,CM,NSE,STK,2,Y,SGBJUN28,GB,100,101,99,100,10\n")
        r = bhavcopy([p], self.p / "out.csv")
        self.assertEqual((r["rows"], r["layout"]), (1, ["udiff"]))
        b = read_bars(self.p / "out.csv")
        self.assertEqual((b[0]["symbol"], b[0]["close"], b[0]["timestamp"]), ("RELIANCE", 1311.0, "2026-11-04T03:45:00+00:00"))

    def test_membership_function(self):
        p = self.p / "m.csv"
        with p.open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["effective_date", "index_type", "inclusions", "exclusions", "symbols"]); w.writeheader()
            w.writerow(dict(effective_date="2020-01-01", index_type="Nifty500", inclusions="A", exclusions="", symbols="A"))
            w.writerow(dict(effective_date="2021-01-01", index_type="Nifty500", inclusions="B", exclusions="A", symbols="B"))
        m = universe.membership(p)
        self.assertEqual((m("A", "2019-12-31"), m("A", "2020-06-01"), m("A", "2021-01-01"), m("B", "2021-02-01")), (False, True, False, True))

    def test_paper_paise_migration_auto_fee_and_mark(self):
        p = self.p / "l.sqlite"
        with sqlite3.connect(p) as c:
            c.execute("CREATE TABLE account (id INTEGER PRIMARY KEY CHECK(id=1), cash REAL NOT NULL)")
            c.execute("CREATE TABLE positions (symbol TEXT PRIMARY KEY, qty INTEGER, cost REAL)")
            c.execute("CREATE TABLE fills (id TEXT PRIMARY KEY, at TEXT, symbol TEXT, side TEXT, qty INTEGER, price REAL, fee REAL, realized REAL)")
            c.execute("INSERT INTO account VALUES (1,0.1+0.2)"); c.execute("INSERT INTO positions VALUES ('X',2,202.0)")
        c.close()
        self.assertEqual(paper.status(p)["cash"], 0.3)
        q = self.p / "n.sqlite"; paper.initialize(q, 10000)
        s = paper.fill(q, "a", "X", "buy", 10, 100, None, "2026-05-04T10:00:00+05:30", "delivery", "discount")
        # buy of 1,000 on delivery, no brokerage: STT 1.00 + stamp 0.15 + exchange 0.0297 + SEBI 0.001 + IPFT 0.001 + GST 0.0057 = 1.19 (paise)
        self.assertAlmostEqual(s["cash"], 10000 - 1000 - 1.19, places=2)
        marked = paper.status(q, {"X": (110, "2026-05-05")})
        self.assertAlmostEqual(marked["unrealized_pnl"], 1100 - 1001.19, places=2)


if __name__ == "__main__":
    unittest.main()
