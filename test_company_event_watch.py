"""No-network regression tests for earnings reminders."""
import unittest
from datetime import date
from company_event_watch import due_events,notify_events

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
        self.assertEqual([x[0] for x in sent].count("TSLA"),1)
        self.assertTrue(all("Geen koopbevestiging" in body for _,body in sent))
        self.assertTrue(all(v["delivery"]=="sent" for v in state["signals"].values()))
    def test_missing_source_does_not_claim_automatic_discovery(self):
        import company_event_watch
        self.assertIn("NOT automatic discovery",company_event_watch.__doc__)
if __name__=="__main__": unittest.main()
