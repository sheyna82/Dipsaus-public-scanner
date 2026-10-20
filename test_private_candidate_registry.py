import unittest
from datetime import datetime, timezone
from private_candidate_registry import validate_registry, audit_private_registry, public_aggregate, reconcile_registry_with_manual_config

NOW = datetime(2026, 10, 20, 15, tzinfo=timezone.utc)

def registry(*rows):
    return {"schema_version": 1, "candidates": list(rows)}

def item(cid, status="ACTIVE", **extra):
    return {"id": cid, "symbol": cid, "status": status, **extra}

class PrivateRegistryTests(unittest.TestCase):
    def test_active_registered_and_deferred_are_retained(self):
        r = audit_private_registry(registry(item("NU"), item("STNE", "REGISTERED")),
            [{"candidate_id": "NU", "status": "FRESH_CHECKED",
              "checked_at": NOW.isoformat()}], now=NOW)
        self.assertEqual(r["summary"]["active"], 2)
        self.assertEqual(r["summary"]["overdue"], 1)

    def test_public_aggregate_never_contains_symbol(self):
        r = audit_private_registry(registry(item("SECRET_TICKER")), [], now=NOW)
        self.assertNotIn("SECRET_TICKER", str(public_aggregate(r)))
        self.assertIn("SECRET_TICKER", str(r["private_details"]))

    def test_closed_requires_reason(self):
        with self.assertRaises(ValueError):
            validate_registry(registry(item("X", "CLOSED")))
        self.assertEqual(len(validate_registry(registry(
            item("X", "CLOSED", closure_reason="USER_REMOVED")))), 1)

    def test_unknown_state_rejected(self):
        with self.assertRaises(ValueError):
            validate_registry(registry(item("X", "GONE")))

    def test_duplicate_id_rejected(self):
        with self.assertRaises(ValueError):
            validate_registry(registry(item("X"), item("X")))

    def test_only_closed_nominations_cannot_claim_complete(self):
        with self.assertRaises(ValueError):
            reconcile_registry_with_manual_config(
                registry(item("A","CLOSED",closure_reason="REMOVED")),{"candidates":{}})

    def test_duplicate_active_symbol_with_different_ids_rejected(self):
        with self.assertRaises(ValueError):
            reconcile_registry_with_manual_config(
                registry({"id":"first","symbol":"A","status":"ACTIVE","monitor_mode":"MANUAL"},
                         {"id":"second","symbol":"A","status":"REGISTERED","monitor_mode":"MANUAL"}),
                {"candidates":{"A":{}}})

    def test_empty_canonical_registry_cannot_claim_complete(self):
        with self.assertRaises(ValueError):
            reconcile_registry_with_manual_config(registry(), {"candidates":{}})

    def test_canonical_nomination_requires_explicit_route(self):
        with self.assertRaises(ValueError):
            reconcile_registry_with_manual_config(
                registry(item("A")), {"candidates":{"A":{}}})

    def test_nominated_manual_symbol_missing_from_scanner(self):
        r=registry(item("A", monitor_mode="MANUAL"),
                   item("B", monitor_mode="MANUAL"))
        result=reconcile_registry_with_manual_config(
            r, {"candidates":{"A":{}}}, {})
        self.assertFalse(result["complete"])
        self.assertEqual(result["missing"],1)
        self.assertEqual(result["private_missing_symbols"],["B"])

    def test_closed_and_discovery_candidates_do_not_require_manual_route(self):
        r=registry(item("A", "CLOSED", closure_reason="REMOVED", monitor_mode="MANUAL"),
                   item("B", monitor_mode="DISCOVERY"),
                   item("C", monitor_mode="MANUAL"))
        result=reconcile_registry_with_manual_config(
            r, {"candidates":{"C":{}}}, {})
        self.assertTrue(result["complete"])
        self.assertEqual(result["required"],1)

    def test_schema_version_required(self):
        with self.assertRaises(ValueError):
            validate_registry({"candidates": []})

    def test_invalid_observations_rejected(self):
        with self.assertRaises(ValueError):
            audit_private_registry(registry(), {}, now=NOW)

if __name__ == "__main__":
    unittest.main()
