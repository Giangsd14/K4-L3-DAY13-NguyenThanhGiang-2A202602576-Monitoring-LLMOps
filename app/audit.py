from __future__ import annotations
import json, uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

AUDIT_FILE = Path('data/audit.jsonl')

def log_audit_event(
    actor: str,
    action: str,
    resource: str,
    status: str = 'SUCCESS',
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
) -> Dict[str, Any]:
    entry = {
        'event_id': str(uuid.uuid4()),
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'actor': actor,
        'action': action,
        'resource': resource,
        'status': status,
        'ip_address': ip_address or '127.0.0.1',
        'details': details or {},
    }
    AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with AUDIT_FILE.open('a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    return entry

def query_audit_events(limit: int = 50, action: Optional[str] = None) -> list[Dict[str, Any]]:
    if not AUDIT_FILE.exists():
        return []
    events = []
    with AUDIT_FILE.open('r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                if action and rec.get('action') != action:
                    continue
                events.append(rec)
            except Exception:
                continue
    return events[-limit:]
