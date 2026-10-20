"""Offline tests for opt-in request pacing."""
import threading
import unittest
from dipsaus_request_pacer import SharedRequestPacer


class PacerTests(unittest.TestCase):
    def test_invalid_interval(self):
        with self.assertRaises(ValueError):
            SharedRequestPacer(-1)

    def test_fake_clock_enforces_spacing(self):
        now=[0.0]
        sleeps=[]
        def sleep(seconds):
            sleeps.append(seconds)
            now[0]+=seconds
        pacer=SharedRequestPacer(0.5,clock=lambda:now[0],sleeper=sleep)
        for _ in range(4):
            pacer.wait()
        self.assertEqual(sleeps,[0.5,0.5,0.5])

    def test_concurrent_waits_are_serialized(self):
        now=[0.0]
        starts=[]
        def sleep(seconds):
            now[0]+=seconds
        pacer=SharedRequestPacer(0.25,clock=lambda:now[0],sleeper=sleep)
        def work():
            pacer.wait()
            with pacer.lock:
                starts.append(now[0])
        threads=[threading.Thread(target=work) for _ in range(8)]
        for thread in threads: thread.start()
        for thread in threads: thread.join()
        self.assertEqual(sorted(starts),[i*0.25 for i in range(8)])


if __name__ == "__main__":
    unittest.main()
