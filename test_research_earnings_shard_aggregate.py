"""Unit tests for fail-closed shard aggregation."""
import json,tempfile,unittest
from pathlib import Path
from research_earnings_shard_aggregate import aggregate

class AggregateTests(unittest.TestCase):
    def make(self,root,name,symbols):
        p=Path(root)/name
        p.write_text(json.dumps({"selected_symbols":len(symbols),"successful_symbols":sum(x["status"]=="downloaded_unverified" for x in symbols),"linked_events":len(symbols),"results":symbols}))
        return p
    def test_distinct_shards(self):
        with tempfile.TemporaryDirectory() as root:
            paths=[self.make(root,f"{i}.json",[{"symbol":f"TEST{i}","status":"downloaded_unverified","event_count":1}]) for i in range(3)]
            result=aggregate(paths)
            self.assertEqual(result["symbols_attempted"],3)
            self.assertEqual(result["symbols_with_prices"],3)
            self.assertEqual(result["distinct_symbols"],3)
            self.assertFalse(result["trade_ready"])
    def test_duplicate_symbol_fails(self):
        with tempfile.TemporaryDirectory() as root:
            symbol={"symbol":"SAME","status":"downloaded_unverified","event_count":1}
            paths=[self.make(root,f"{i}.json",[symbol]) for i in range(2)]
            with self.assertRaisesRegex(ValueError,"overlapping_shards"):
                aggregate(paths)
if __name__=="__main__":unittest.main()
