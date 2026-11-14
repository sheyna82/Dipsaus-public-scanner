import base64
import hashlib
import json
import unittest
from research_validate_omxh25_real_history_post import validate

def fixture():
    body = {"sEcho":1,"iTotalRecords":1,"iTotalDisplayRecords":1,
            "aaData":[{"TradeDate":"2026-11-06T00:00:00",
                       "TimeStamp":"2026-11-06T00:00:00","Value":6221.79256147799,
                       "Close":None,"Currency":"EUR","IndexIsin":"FI0008900212"}]}
    raw = json.dumps(body).encode()
    return {"schema":"dipsaus_omxh25_history_post_candidate_v1",
            "source_url":"https://beta.indexes.nasdaqomx.com/Index/HistoryData",
            "http_method":"POST","http_status":200,"content_type":"application/json",
            "request_fields":{"id":"OMXH25","startDate":"2026-11-05T00:00:00.000",
                              "endDate":"2026-11-09T00:00:00.000","timeOfDay":"EOD"},
            "source_raw_base64":base64.b64encode(raw).decode(),
            "source_sha256":hashlib.sha256(raw).hexdigest()}

def mutate_body(receipt, change):
    body = json.loads(base64.b64decode(receipt["source_raw_base64"]))
    change(body)
    raw = json.dumps(body).encode()
    receipt["source_raw_base64"] = base64.b64encode(raw).decode()
    receipt["source_sha256"] = hashlib.sha256(raw).hexdigest()

class RealHistoryTests(unittest.TestCase):
    def test_valid_raw_schema_remains_research_only(self):
        result = validate(fixture())
        self.assertEqual(result["record_count"], 1)
        self.assertTrue(result["official_eod_raw_bytes_verified"])
        self.assertFalse(result["benchmark_identity_verified"])
        self.assertFalse(result["trade_ready"])

    def test_tampered_hash(self):
        receipt = fixture()
        receipt["source_sha256"] = "0"*64
        with self.assertRaisesRegex(ValueError, "RAW_HASH_MISMATCH"):
            validate(receipt)

    def test_wrong_isin(self):
        receipt = fixture()
        mutate_body(receipt, lambda body: body["aaData"][0].update(IndexIsin="WRONG"))
        with self.assertRaisesRegex(ValueError, "INDEX_IDENTITY"):
            validate(receipt)

    def test_wrong_date(self):
        receipt = fixture()
        mutate_body(receipt, lambda body: body["aaData"][0].update(TradeDate="2026-11-10T00:00:00", TimeStamp="2026-11-10T00:00:00"))
        with self.assertRaisesRegex(ValueError, "OUT_OF_RANGE"):
            validate(receipt)

    def test_wrong_count(self):
        receipt = fixture()
        mutate_body(receipt, lambda body: body.update(iTotalRecords=2))
        with self.assertRaisesRegex(ValueError, "RECORD_COUNT"):
            validate(receipt)

    def test_invalid_value(self):
        receipt = fixture()
        mutate_body(receipt, lambda body: body["aaData"][0].update(Value=-1))
        with self.assertRaisesRegex(ValueError, "INDEX_VALUE"):
            validate(receipt)

if __name__ == "__main__":
    unittest.main()
