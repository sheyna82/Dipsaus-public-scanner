"""Mocked GitHub artifact pagination and restoration; no network access."""
import gzip
import json
import unittest
from pathlib import Path
from unittest.mock import patch
import incremental_database as mod

class RestorePaginationTests(unittest.TestCase):
    def test_second_page_archive_is_discovered(self):
        pages=[]
        for i in range(100):
            pages.append({"id":i+1,"name":"unrelated","created_at":"2026-10-28T00:00:00Z"})
        pages.append({"id":501,"name":"ohlcv-incremental","created_at":"2026-10-27T00:00:00Z","workflow_run":{"id":123}})
        calls=[]
        def fake_get(url,authenticated=False):
            calls.append(url)
            page=int(url.split("&page=")[-1])
            return json.dumps({"artifacts":pages[(page-1)*100:page*100]}).encode()
        def fake_run(cmd,**kwargs):
            folder=Path(cmd[cmd.index("-D")+1])
            with gzip.open(folder/"ohlcv.jsonl.gz","wt",encoding="utf-8") as f:
                f.write(json.dumps({"symbol":"ABC","bars":[["2026-01-02",10,12,9,11,100]]})+"\\n")
            return type("Result",(),{"returncode":0,"stderr":""})()
        with patch.object(mod,"TOKEN","mock-token"),patch.object(mod,"get",side_effect=fake_get),patch.object(mod.subprocess,"run",side_effect=fake_run):
            records,note=mod.restore()
        self.assertEqual(len(calls),2)
        self.assertIn("&page=2",calls[1])
        self.assertEqual(list(records),["ABC"])
        self.assertIn("501",note)
    def test_incomplete_inventory_fails_closed(self):
        batch=[{"id":i,"name":"unrelated"} for i in range(100)]
        with patch.object(mod,"TOKEN","mock-token"),patch.object(mod,"get",return_value=json.dumps({"artifacts":batch}).encode()):
            with self.assertRaisesRegex(RuntimeError,"pagination limit reached"):
                mod.restore()
if __name__=="__main__":unittest.main()
