"""No-network regression tests for earnings reminders."""
import unittest
from datetime import date
from company_event_watch import due_events,notify_events,discover_earnings,refresh_discovered_events

class FakeStore:
    def __init__(self): self.saved=0
    def require_exclusive_sender(self): pass
    def save(self,state): self.saved+=1

class EventWatchTests(unittest.TestCase):
    def test_pre_event(self):
        self.assertIn(("TSLA","2026-10-21","Q3 results after US close","https://ir.tesla.com/","TOMORROW"),list(due_events(date(2026,10,20))))
    def test_event_and_post(self):
        self.assertTrue(any(x[0]=="PLTR" and x[-1]=="TODAY" for x in due_events(date(2026,11,2))))
        self.assertTrue(any(x[0]=="PLTR" and x[-1]=="POST_EVENT" for x in due_events(date(2026,11,3))))
    def test_no_unrelated_day(self):
        self.assertEqual(list(due_events(date(2026,12,1))),[])
    def test_dedup_and_no_trade_instruction(self):
        store=FakeStore();state={"signals":{}};sent=[]
        sender=lambda symbol,body:sent.append((symbol,body))
        notify_events(store,state,sender,date(2026,10,20))
        notify_events(store,state,sender,date(2026,10,20))
        self.assertEqual([x[0] for x in sent].count("TSLA"),2)
        self.assertEqual(len([k for k in state["signals"] if k.startswith("EVENT|TSLA|")]),1)
        self.assertEqual(len([k for k in state["signals"] if k.startswith("EVENT_RESEARCH|TSLA|")]),1)
        self.assertTrue(all("Geen koopbevestiging" in body for _,body in sent))
        self.assertTrue(all(v["delivery"]=="sent" for v in state["signals"].values()))
    def test_discovery_filters_and_marks_estimates(self):
        def fetch(_):
            return {"earningsCalendar":[
              {"symbol":"WRBY","date":"2026-10-23"},
              {"symbol":"TSLA","date":"2026-10-21"},
              {"symbol":"OTHER","date":"2026-10-23"},
              {"symbol":"ARQT","date":"invalid"}]}
        found=discover_earnings(["WRBY","TSLA","ARQT"],date(2026,10,19),fetch)
        self.assertEqual(len(found),1)
        self.assertEqual(found[0][0],"WRBY")
        self.assertEqual(found[0][-1],"ESTIMATED")
    def test_provider_failure_fails_closed(self):
        self.assertEqual(discover_earnings(["WRBY"],date(2026,10,19),
            lambda _: {"error":"rate limit"}),[])
    def test_cached_calendar_on_provider_failure(self):
        from unittest.mock import patch
        import json
        from pathlib import Path
        cache={"company_event_calendar":{"checked_day":"2026-10-18",
            "events":[["WRBY","2026-10-23","Earnings estimate","https://finnhub.io/","ESTIMATED"]]}}
        with patch("company_event_watch.Path.read_text",return_value=json.dumps(
            {"auto_us_notify_watchlist":["WRBY"],"auto_us_silent_follow":[]})):
            result=refresh_discovered_events(cache,date(2026,10,19),lambda _: {})
        self.assertEqual(len(result),1)
if __name__=="__main__": unittest.main()
