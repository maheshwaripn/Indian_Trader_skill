import csv
import json
import math
import tempfile
import unittest
from pathlib import Path
from indian_trader import bank, coach, paper, research, universe
from indian_trader.cli import demo
from indian_trader.core import read_bars
from indian_trader.providers import save
from indian_trader.report import dashboard


def bars(closes, opens=None):
    rows=[]
    for i,c in enumerate(closes):
        o=opens[i] if opens else c
        rows.append(dict(timestamp=f"2024-01-{i+1:02d}T03:45:00+00:00",symbol="TEST",open=o,high=max(o,c),low=min(o,c),close=c,volume=1000))
    return rows


class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.p=Path(self.tmp.name)
    def tearDown(self):
        self.tmp.cleanup()
    def test_demo_reproducible(self):
        demo(self.p/'a.csv');demo(self.p/'b.csv')
        self.assertEqual((self.p/'a.csv').read_bytes(),(self.p/'b.csv').read_bytes())
    def test_duplicate_rejected(self):
        b=bars([10]);save(b+b,self.p/'b.csv')
        with self.assertRaisesRegex(ValueError,'duplicate'):read_bars(self.p/'b.csv')
    def test_nan_rejected(self):
        b=bars([10]);b[0]['close']=float('nan');save(b,self.p/'b.csv')
        with self.assertRaises(ValueError):read_bars(self.p/'b.csv')
    def test_bad_ohlc_rejected(self):
        b=bars([10]);b[0]['low']=11;save(b,self.p/'b.csv')
        with self.assertRaises(ValueError):read_bars(self.p/'b.csv')
    def test_naive_time_rejected(self):
        b=bars([10]);b[0]['timestamp']='2024-01-01T09:15:00';save(b,self.p/'b.csv')
        with self.assertRaises(ValueError):read_bars(self.p/'b.csv')
    def test_row_budget(self):
        save(bars([10,11]),self.p/'b.csv')
        with self.assertRaisesRegex(ValueError,'budget'):read_bars(self.p/'b.csv',1)
    def test_no_same_close_entry(self):
        b=bars([10,9,11,12,13])
        r=research.run(b,lookback=2,stop_pct=20,target_r=10,fee_bps=0,slippage_bps=0)
        self.assertEqual(r['trades'][0]['entry_time'],b[3]['timestamp'])
        self.assertEqual(r['trades'][0]['entry'],12)
    def test_costs_reduce_returns(self):
        b=bars([10,9,11,12,13])
        zero=research.run(b,lookback=2,fee_bps=0,slippage_bps=0)
        cost=research.run(b,lookback=2,fee_bps=20,slippage_bps=10)
        self.assertLess(cost['metrics']['net_pnl'],zero['metrics']['net_pnl'])
    def test_gap_stop(self):
        b=bars([10,9,11,12,8])
        r=research.run(b,lookback=2,stop_pct=10,target_r=10,fee_bps=0,slippage_bps=0)
        self.assertEqual(r['trades'][0]['exit'],8)
        self.assertEqual(r['trades'][0]['reason'],'gap_stop')
    def test_ambiguous_stop_first(self):
        b=bars([10,9,11,12,12]);b[3]['low']=8;b[3]['high']=20
        r=research.run(b,lookback=2,stop_pct=10,target_r=2,fee_bps=0,slippage_bps=0)
        self.assertEqual(r['trades'][0]['reason'],'stop_first_if_ambiguous')
    def test_accounting_identity(self):
        demo(self.p/'a.csv');r=research.run(read_bars(self.p/'a.csv'))
        self.assertAlmostEqual(sum(t['net_pnl'] for t in r['trades']),r['metrics']['net_pnl'],places=5)
    def test_zero_trades_no_fake_metrics(self):
        r=research.run(bars([10,10,10]),lookback=2)
        self.assertEqual(r['metrics']['trades'],0)
        self.assertIsNone(r['metrics']['win_rate_pct'])
    def test_incomplete_orb_rejected(self):
        with self.assertRaisesRegex(ValueError,'complete'):research.run(bars([10,11]),strategy='orb')
    def test_orb_next_bar_and_flat(self):
        from datetime import datetime,timedelta,timezone
        start=datetime(2024,1,2,9,15,tzinfo=timezone(timedelta(hours=5,minutes=30)))
        b=[]
        for i in range(75):
            p=100 if i<3 else 101
            b.append(dict(timestamp=(start+timedelta(minutes=5*i)).isoformat(),symbol='ORB',open=p,high=p+.1,low=p-.1,close=p,volume=1000))
        r=research.run(b,strategy='orb',stop_pct=10,target_r=10)
        self.assertEqual(len(r['trades']),1)
        self.assertEqual(r['trades'][0]['entry_time'],b[4]['timestamp'])
        self.assertEqual(r['trades'][0]['reason'],'session_close_proxy')
    def test_paper_duplicate_and_oversell(self):
        p=self.p/'paper.sqlite';paper.initialize(p,1000)
        paper.fill(p,'one','X','buy',2,100,1)
        with self.assertRaises(ValueError):paper.fill(p,'one','X','buy',2,100,1)
        with self.assertRaises(ValueError):paper.fill(p,'two','X','sell',3,110,1)
        s=paper.fill(p,'three','X','sell',2,110,1)
        self.assertEqual(s['cash'],1018);self.assertEqual(s['realized_pnl'],18)
        self.assertEqual(s['fills'],2)
    def test_paper_insufficient_cash(self):
        p=self.p/'paper.sqlite';paper.initialize(p,100)
        with self.assertRaises(ValueError):paper.fill(p,'x','X','buy',2,100,0)
        self.assertEqual(paper.status(p)['cash'],100)
    def test_paper_invalid_numeric(self):
        p=self.p/'paper.sqlite';paper.initialize(p,100)
        with self.assertRaises(ValueError):paper.fill(p,'x','X','buy',1,float('nan'),0)
    def test_bank_idempotent_and_tamper(self):
        demo(self.p/'a.csv');root=self.p/'bank'
        a=bank.ingest(root,'demo',self.p/'a.csv','synthetic',1000)
        bank.ingest(root,'demo',self.p/'a.csv','synthetic',1000)
        self.assertEqual(len(bank.catalogue(root)),1)
        self.assertTrue(bank.verify(root)[0]['ok'])
        Path(a['path']).write_text('corrupted')
        self.assertFalse(bank.verify(root)[0]['ok'])
    def test_universe_conflict_and_no_future(self):
        p=self.p/'u.csv'
        with p.open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=['effective_date','index_type','inclusions','exclusions','symbols']);w.writeheader()
            w.writerow(dict(effective_date='2020-01-01',index_type='Nifty500',inclusions='A',exclusions='',symbols='A'))
            w.writerow(dict(effective_date='2021-01-01',index_type='Nifty500',inclusions='B',exclusions='A',symbols='A,B'))
        self.assertEqual(universe.audit(p)['transition_mismatches'],1)
        with self.assertRaises(ValueError):universe.asof(p,'2020-06-01')
        self.assertEqual(universe.asof(p,'2020-06-01',allow_unverified=True)['symbols'],['A'])
        with self.assertRaises(ValueError):universe.asof(p,'2019-01-01',allow_unverified=True)
    def test_dashboard_escapes_external_strings(self):
        r=research.run(bars([10,10,10]),lookback=2);r['strategy']='<script>alert(1)</script>'
        dashboard(r,self.p/'r.html')
        text=(self.p/'r.html').read_text()
        self.assertNotIn('<script>alert(1)',text)
        self.assertIn('&lt;script&gt;',text)
    def test_out_of_order_rejected(self):
        b=bars([10,11]);save(list(reversed(b)),self.p/'b.csv')
        with self.assertRaisesRegex(ValueError,'increase'):read_bars(self.p/'b.csv')
    def test_bhavcopy_conversion_and_unknown_format(self):
        from indian_trader.providers import bhavcopy
        p=self.p/'nse.csv'
        p.write_text('SYMBOL,SERIES,OPEN,HIGH,LOW,CLOSE,TOTTRDQTY,TIMESTAMP\nDEMO,EQ,10,12,9,11,100,02-Jan-2024\n')
        bhavcopy(p,self.p/'canonical.csv')
        b=read_bars(self.p/'canonical.csv')
        self.assertEqual(b[0]['symbol'],'DEMO')
        self.assertEqual(b[0]['timestamp'],'2024-01-02T03:45:00+00:00')
        p.write_text('unexpected,columns\n1,2\n')
        with self.assertRaisesRegex(ValueError,'legacy'):bhavcopy(p,self.p/'bad.csv')
    def test_paper_partial_sale_cost_basis(self):
        p=self.p/'paper.sqlite';paper.initialize(p,1000)
        paper.fill(p,'one','X','buy',4,100,4)
        r=paper.fill(p,'two','X','sell',2,110,2)
        self.assertEqual(r['realized_pnl'],16)
        self.assertEqual(r['positions'][0]['cost_basis'],202)
        self.assertEqual(r['positions'][0]['qty'],2)
    def test_coach_flags_placeholders(self):
        spec={k:"specified" for k in coach.REQUIRED};spec["entry"]="RSI period unresolved"
        self.assertEqual(coach.review(spec)["unresolved_fields"],["entry"])
        self.assertEqual(coach.review(spec)["status"],"INCOMPLETE")
    def test_coach_is_not_profit_claim(self):
        r=coach.review({});self.assertEqual(r['status'],'INCOMPLETE');self.assertEqual(len(r['missing']),10)

if __name__=='__main__':unittest.main()
