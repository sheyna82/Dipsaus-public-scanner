import unittest
from datetime import datetime,timezone
from research.us_evidence_chain_report_20261117 import review_us_evidence_chain
NOW=datetime(2026,11,17,15,20,tzinfo=timezone.utc)
T="2026-11-17T15:00:00+00:00"
def docs():
    return ({"generated_utc":T,"candidates":[{"symbol":"TEST"}]},
            {"generated_utc":T,"rows":[{"symbol":"TEST","discovery_lane":"FAST-MOMENTUM-RECOVERY"}]},
            {"generated_utc":T,"rows":[{"symbol":"TEST","route_type":"EARLY-MOMENTUM-RECOVERY-VERIFY"}]})
def calendar():
    return {"session_date":"2026-11-17","session_kind":"regular","exchange":"XNAS",
            "source_url":"https://example.org/calendar","retrieval_reference":"fixture",
            "retrieved_utc":T}
class EvidenceChainTests(unittest.TestCase):
    def review(self,documents=None,record=None):
        return review_us_evidence_chain(*(documents if documents is not None else docs()),
                                        calendar() if record is None else record,
                                        session_date="2026-11-17",now=NOW)
    def test_existing_shape_blocks_missing_provenance(self):
        r=self.review()
        self.assertIn("END_TO_END_PROVENANCE_UNVERIFIED",r["blocks"])
        self.assertEqual(r["route_count"],1)
    def test_calendar_metadata_never_authorizes(self):
        r=self.review()
        self.assertIn("OFFICIAL_EXCHANGE_CALENDAR_UNVERIFIED",r["blocks"])
        self.assertFalse(r["trade_ready"])
    def test_broker_and_net_checks_remain_blocked(self):
        r=self.review()
        self.assertIn("EUR_NET_PROFIT_AND_RR_UNVERIFIED",r["blocks"])
        self.assertIn("BROKER_BID_ASK_UNVERIFIED",r["blocks"])
        self.assertFalse(r["notify"])
    def test_missing_calendar_blocks(self):
        r=self.review(record={})
        self.assertIn("CHAIN_SESSION_KIND_UNSUPPORTED",r["blocks"])
    def test_no_routes_not_complete(self):
        d,h,r=docs();r["rows"]=[]
        x=self.review(documents=(d,h,r))
        self.assertFalse(x["provenance_complete"])
        self.assertEqual(x["route_count"],0)
if __name__=="__main__":
    unittest.main()
