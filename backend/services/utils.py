from datetime import datetime, timezone
from typing import Optional


def parse_date(d_str) -> Optional[str]:
    """Try to extract a YYYY-MM-DD date string from various date formats."""
    if not d_str:
        return None
    if isinstance(d_str, (int, float)):
        try:
            return datetime.utcfromtimestamp(d_str).strftime('%Y-%m-%d')
        except Exception:
            return None
    for fmt in ('%Y-%m-%dT%H:%M:%SZ', '%a, %d %b %Y %H:%M:%S %z', '%Y-%m-%d'):
        try:
            return datetime.strptime(str(d_str)[:25], fmt).strftime('%Y-%m-%d')
        except Exception:
            continue
    return str(d_str)[:10]  # fallback: take first 10 chars
