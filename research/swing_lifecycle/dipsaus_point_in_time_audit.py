"""Point-in-time chronology checks; research-only, no trading orders."""
import csv
from datetime import datetime, timezone

FIELDS = ("symbol","decision_at","feature_available_at","entry_at","exit_at","outcome_available_at")
def parse_time(value):
    dt=datetime.fromisoformat(value.replace("Z","+00:00"))
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError("timezone offset required")
    return dt.astimezone(timezone.utc)
def audit_rows(rows, training_cutoff=None):
    cutoff=parse_time(training_cutoff) if training_cutoff else None
    issues=[]
    for index,row in enumerate(rows,1):
        try:
            t={key:parse_time(row[key]) for key in FIELDS[1:]}
            if not row["symbol"].strip(): issues.append((index,"MISSING_SYMBOL"))
        except (KeyError,ValueError,TypeError,AttributeError):
            issues.append((index,"INVALID_TIMESTAMP_OR_FIELD"));continue
        for failed,name in (
            (t["feature_available_at"]>t["decision_at"],"FUTURE_FEATURE"),
            (t["entry_at"]<t["decision_at"],"ENTRY_BEFORE_DECISION"),
            (t["exit_at"]<t["entry_at"],"EXIT_BEFORE_ENTRY"),
            (t["outcome_available_at"]<t["exit_at"],"OUTCOME_BEFORE_EXIT"),
            (bool(cutoff and t["decision_at"]<cutoff and t["outcome_available_at"]>=cutoff),"TRAINING_LABEL_NOT_YET_KNOWN")):
            if failed:issues.append((index,name))
    return issues
def audit_csv(path,training_cutoff=None):
    with open(path,newline="",encoding="utf-8-sig") as handle:
        return audit_rows(csv.DictReader(handle),training_cutoff)
