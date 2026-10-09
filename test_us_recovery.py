import unittest
from datetime import datetime, timezone
from us_execution_gate import evaluate_trade
from us_recovery_map import recovery_map
from us_research_triage import research_queue
from us_news_fallback import KEYWORDS
from us_candidate_dossier import dossier
from us_company_profile import company_profile
from us_identity_check import identity_check
from us_news_relevance import classify_headlines, classify_event_materiality
from us_event_research import sec_headers, ticker_ciks, filing_content_review
from unittest.mock import patch

class GateTests(unittest.TestCase):
    def evidence(self):
        return dict(symbol="TEST",quote_utc="2026-09-23T18:00:00+00:00",
          ask_usd=100,bid_usd=99.9,eur_per_usd=.9,fx_utc="2026-09-23T18:00:00+00:00",
          invalidation_usd=96,first_meaningful_resistance_usd=103,
          realistic_target_usd=110,bottom_confirmed=True,daily_weekly_reviewed=True,
          resistance_confirmed=True,company_event_risk_verified=True,
          recent_price_moving_news_verified=True,upcoming_material_events_verified=True,
          corporate_actions_verified=True,portfolio_fit_verified=True,
          broker_quote_verified=True,fx_verified=True)
    def test_missing_is_blocked(self):
        self.assertEqual(evaluate_trade({})["status"],"DATA_BLOCKED")
    def test_stale_is_blocked(self):
        self.assertEqual(evaluate_trade(self.evidence(),now=datetime(2026,9,23,18,6,tzinfo=timezone.utc))["status"],"STALE_OR_FUTURE_DATA")
    def test_missing_risk_cap_blocks(self):
        x=evaluate_trade(self.evidence(),now=datetime(2026,9,23,18,1,tzinfo=timezone.utc))
        self.assertEqual(x["status"],"MONEY_OR_RISK_BLOCKED")
        self.assertFalse(x["trade_ready"])
    def test_eur_math_and_manual_review(self):
        x=evaluate_trade(self.evidence(),now=datetime(2026,9,23,18,1,tzinfo=timezone.utc),max_risk_eur=150)
        self.assertEqual(x["whole_shares"],38)
        self.assertEqual(x["target_gross_eur"],342)
        self.assertEqual(x["status"],"HUMAN_REVIEW_REQUIRED")
        self.assertFalse(x["trade_ready"])
    def test_friction_below_entry_blocks(self):
        e=self.evidence();e["first_meaningful_resistance_usd"]=99
        self.assertEqual(evaluate_trade(e,now=datetime(2026,9,23,18,1,tzinfo=timezone.utc),max_risk_eur=150)["status"],"STRUCTURE_BLOCKED")
    def test_map_is_never_trade_ready(self):
        rows=[dict(date=(datetime(2026,1,1,tzinfo=timezone.utc).date()).isoformat(),open=10,high=11,low=9,close=10,volume=100)]*65
        self.assertFalse(recovery_map(rows)["trade_ready"])
class TriageTests(unittest.TestCase):
    def test_strategic_news_flag_vocabulary(self):
        self.assertIn("strategic review", KEYWORDS)
        self.assertIn("special committee", KEYWORDS)
    def test_penny_stock_retained_but_not_prioritized(self):
        def candidate(symbol,price):
            return {"symbol":symbol,"last_close_usd":price,"average_20d_volume_shares":1000000,
              "research_triage":{"space_to_first_overhead_pct":5},
              "recovery_map":{"weekly_structure":{"completed_week_close_rising":True,"completed_week_higher_low":True},"bottom_signal_count":3}}
        names=[candidate("PENNY",.22),candidate("ORDINARY",30)]
        queue,excluded=research_queue(names)
        self.assertEqual([x["symbol"] for x in queue],["ORDINARY"])
        self.assertIn("PENNY",excluded["liquidity_review"])
        self.assertEqual(len(names),2)
class DossierTests(unittest.TestCase):
    def test_dossier_never_clears_news_or_portfolio(self):
        c={"symbol":"TEST","name":"Test Inc","last_bar_date":"2026-09-23",
           "last_close_usd":30,"liquidity_triage":{"flags":[]},
           "research_triage":{"first_overhead_reference_usd":33,"space_to_first_overhead_pct":10},
           "recovery_map":{"bottom_signal_count":3,"historical_overhead_pivot_zones":[],
             "weekly_structure":{"completed_week_close_rising":True,"completed_week_higher_low":False}}}
        q={"event_research":{"status":"SEC_TICKER_MAP_UNAVAILABLE"},
           "alternative_event_research":{"news_status":"FETCHED","earnings_status":"EMPTY_UNVERIFIED",
             "headline_review":[{"headline":"Strategic review","keyword_flag":True}],"earnings_dates":[]}}
        result=dossier(c,q)
        self.assertEqual(result["company_event"]["flagged_headlines"][0]["headline"],"Strategic review")
        self.assertFalse(result["company_event"]["event_risk_cleared"])
        self.assertEqual(result["portfolio_fit"]["status"],"NOT_VERIFIED")
        self.assertFalse(result["trade_ready"])
class CompanyProfileTests(unittest.TestCase):
    def test_missing_key_fails_closed(self):
        with patch.dict("os.environ",{"FINNHUB_API_KEY":""}):
            x=company_profile("TEST",token="")
        self.assertEqual(x["status"],"NO_API_KEY")
        self.assertFalse(x["financial_quality_verified"])
    def test_ticker_mismatch_fails_closed(self):
        with patch("us_company_profile._fetch",return_value={"ticker":"OTHER","name":"Other"}):
            x=company_profile("TEST",token="fake")
        self.assertEqual(x["status"],"TICKER_MISMATCH")
        self.assertFalse(x["issuer_identity_verified"])
    def test_profile_never_clears_financial_or_portfolio(self):
        with patch("us_company_profile._fetch",return_value={"ticker":"TEST","name":"Test Co","finnhubIndustry":"Industrials"}):
            x=company_profile("TEST",token="fake")
        self.assertEqual(x["industry"],"Industrials")
        self.assertFalse(x["financial_quality_verified"])
        self.assertFalse(x["portfolio_fit_verified"])
class IdentityTests(unittest.TestCase):
    def profile(self,name,symbol="GNRC"):
        return {"status":"PROFILE_RESEARCH_AVAILABLE","issuer_name":name,"profile_symbol":symbol}
    def test_wrong_company_same_ticker_blocked(self):
        x=identity_check("GNRC","Generac Holdings Inc - Common Stock",self.profile("Honeywell International Inc"))
        self.assertEqual(x["status"],"IDENTITY_MISMATCH")
        self.assertFalse(x["issuer_identity_verified"])
    def test_legitimate_legal_suffix_variation(self):
        x=identity_check("AMSC","American Superconductor Corporation - Common Stock",
                         {"status":"PROFILE_RESEARCH_AVAILABLE","issuer_name":"American Superconductor Corp","profile_symbol":"AMSC"})
        self.assertEqual(x["status"],"NAME_CONSISTENT_UNVERIFIED")
        self.assertFalse(x["issuer_identity_verified"])
    def test_symbol_mismatch_blocks(self):
        x=identity_check("GNRC","Generac Holdings Inc",self.profile("Generac Holdings Inc","HON"))
        self.assertEqual(x["status"],"IDENTITY_MISMATCH")
class NewsRelevanceTests(unittest.TestCase):
    def test_generic_and_other_issuer_not_automatically_material(self):
        news={"flagged_headline_review":[{"headline":"Forget Overvalued Tech: Build an AI Fortress Portfolio With These 5 Dividend Aristocrats"},{"headline":"Silicon Motion reports results"}]}
        profile={"status":"PROFILE_RESEARCH_AVAILABLE","issuer_name":"Honeywell International Inc"}
        x=classify_headlines(news,profile)
        self.assertEqual(len(x["issuer_specific"]),0)
        self.assertEqual(len(x["not_issuer_specific"]),1)
        self.assertEqual(len(x["unresolved"]),1)
        self.assertFalse(x["event_risk_cleared"])
    def test_named_issuer_is_only_review_signal(self):
        x=classify_headlines({"flagged_headline_review":[{"headline":"Honeywell announces restructuring"}]},{"status":"PROFILE_RESEARCH_AVAILABLE","issuer_name":"Honeywell International Inc"})
        self.assertEqual(len(x["issuer_specific"]),1)
        self.assertFalse(x["event_risk_cleared"])
class NewsEventTriageTests(unittest.TestCase):
    def test_analysis_is_not_concrete_event(self):
        x=classify_event_materiality({"issuer_specific":[{"headline":"Cerebras Stock Has Been Cut in Half. It Still Costs About 145 Times Next Year's Estimated Earnings."},{"headline":"Cerebras (CBRS) Down 17.2% Since Last Earnings Report: Can It Rebound?"}]})
        self.assertEqual(len(x["analysis_or_commentary"]),2)
        self.assertFalse(x["potential_concrete_events"])
        self.assertFalse(x["event_risk_cleared"])
    def test_specific_action_prioritized_but_not_verified(self):
        x=classify_event_materiality({"issuer_specific":[{"headline":"Honeywell announces restructuring"},{"headline":"Honeywell earnings beat expectations"}]})
        self.assertEqual(len(x["potential_concrete_events"]),1)
        self.assertEqual(len(x["ambiguous_issuer_news"]),1)
        self.assertFalse(x["event_occurrence_verified"])
class SecAccessTests(unittest.TestCase):
    def test_no_contact_makes_no_network_request(self):
        with patch.dict("os.environ",{"SEC_CONTACT_EMAIL":""}):
            with patch("us_event_research.urllib.request.urlopen") as network:
                with self.assertRaisesRegex(RuntimeError,"SEC_CONTACT_EMAIL_NOT_CONFIGURED"):
                    ticker_ciks()
                network.assert_not_called()
    def test_configured_contact_in_user_agent(self):
        with patch.dict("os.environ",{"SEC_CONTACT_EMAIL":"research@example.org"}):
            self.assertEqual(sec_headers()["User-Agent"],"Dipsaus Research Scanner research@example.org")
    def test_invalid_contact_rejected(self):
        with patch.dict("os.environ",{"SEC_CONTACT_EMAIL":"invalid contact"}):
            with self.assertRaisesRegex(RuntimeError,"SEC_CONTACT_EMAIL_NOT_CONFIGURED"):
                sec_headers()
class FilingContentTests(unittest.TestCase):
    def test_invalid_url_does_not_fetch(self):
        with patch("us_event_research.urllib.request.urlopen") as network:
            x=filing_content_review({"url":"https://evil.example/test"})
            self.assertEqual(x["status"],"INVALID_SEC_ARCHIVE_URL")
            network.assert_not_called()
    def test_excerpt_never_clears_risk(self):
        from unittest.mock import MagicMock
        response=MagicMock()
        response.__enter__.return_value.read.return_value=b"<html><body><h1>Item 8.01</h1><p>"+b"Material agreement details. "*20+b"</p></body></html>"
        with patch.dict("os.environ",{"SEC_CONTACT_EMAIL":"research@example.org"}):
            with patch("us_event_research.urllib.request.urlopen",return_value=response):
                x=filing_content_review({"url":"https://www.sec.gov/Archives/edgar/data/880807/000143774926030822/test.htm","item_codes":["8.01"]})
        self.assertEqual(x["status"],"EXCERPT_REQUIRES_HUMAN_REVIEW")
        self.assertIn("Material agreement",x["excerpt"])
        self.assertFalse(x["event_risk_cleared"])
class BatchInputTests(unittest.TestCase):
    def test_batch_one_is_not_zero(self):
        from us_recovery_pilot import parse_batch
        self.assertEqual(parse_batch("1"),1)
        self.assertEqual(list(range(42))[parse_batch("1")::21],[1,22])
    def test_missing_and_invalid_batch_fail_closed(self):
        from us_recovery_pilot import parse_batch
        for value in (None,"","21","-1","one","1.0"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    parse_batch(value)

class SoldOffDiscoveryTests(unittest.TestCase):
    def test_sofi_regression_case_surfaces_before_plus_one_day(self):
        from us_momentum_recovery_discovery import discovery_gate
        # SOFI-like regression fixture: heavily sold off, liquid, modest rebound,
        # flat/red session, and no completed intraday structure yet.
        keep,sold_off=discovery_gate(-30.0,0.3,500_000_000,-0.6,False)
        self.assertTrue(keep)
        self.assertTrue(sold_off)
    def test_nio_regression_low_nominal_price_can_enter_discovery_gate(self):
        from us_momentum_recovery_discovery import discovery_gate
        # NIO-like case: nominal share price below $5 must not itself block discovery.
        # Market-cap and dollar-turnover quality gates are enforced by the scanner.
        keep,sold_off=discovery_gate(-35.0,5.0,90_000_000,0.5,False)
        self.assertTrue(keep)
        self.assertTrue(sold_off)
    def test_shallow_dip_does_not_enter_sold_off_lane(self):
        from us_momentum_recovery_discovery import discovery_gate
        keep,sold_off=discovery_gate(-9.0,0.3,500_000_000,-0.6,False)
        self.assertFalse(keep)
        self.assertFalse(sold_off)
if __name__=="__main__":unittest.main()

