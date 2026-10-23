"""Read-only scanner workflow inventory; does not run or modify workflows."""
from pathlib import Path

WORKFLOWS = {
    "prealert": ".github/workflows/shadow-prealert.yml",
    "eu": ".github/workflows/shadow-eu.yml",
    "us": ".github/workflows/shadow-us.yml",
}
REQUIRED = ("concurrency:", "timeout-minutes:", "SCANNER_NOTIFICATIONS_ENABLED:")


def audit_workflows(root):
    results = {}
    for name, rel in WORKFLOWS.items():
        path = Path(root) / rel
        if not path.is_file():
            results[name] = {"status": "UNKNOWN", "reason": "MISSING_WORKFLOW"}
            continue
        data = path.read_text(encoding="utf-8")
        absent = [key for key in REQUIRED if key not in data]
        if absent:
            results[name] = {"status": "UNKNOWN", "reason": "MISSING_SAFETY_DECLARATION",
                             "missing": absent}
            continue
        notify_line = next((x.strip() for x in data.splitlines()
                            if x.strip().startswith("SCANNER_NOTIFICATIONS_ENABLED:")), "")
        results[name] = {
            "status": "CONFIG_OBSERVED",
            "notification_setting": notify_line.split(":", 1)[1].strip(),
            "has_schedule": any(x.strip().startswith("- cron:") for x in data.splitlines()),
            "has_concurrency": True, "has_timeout": True,
            "delivery_confirmed": False,
        }
    return {"status": "STATIC_INVENTORY_ONLY", "workflows": results,
            "delivery_confirmed": False, "predictive_quality_confirmed": False,
            "trade_ready": False}


if __name__ == "__main__":
    import json
    print(json.dumps(audit_workflows(Path(__file__).parent), sort_keys=True))
