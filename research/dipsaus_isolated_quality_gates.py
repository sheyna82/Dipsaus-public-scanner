"""Research-only quality gate; fail closed."""
from datetime import datetime, timezone

def check_age(stamp, now, max_seconds=120):
    try:
        dt=datetime.fromisoformat(stamp.replace('Z','+00:00'))
        if dt.tzinfo is None: return False
        age=(now.astimezone(timezone.utc)-dt.astimezone(timezone.utc)).total_seconds()
        return 0<=age<=max_seconds
    except (ValueError,TypeError,AttributeError): return False
