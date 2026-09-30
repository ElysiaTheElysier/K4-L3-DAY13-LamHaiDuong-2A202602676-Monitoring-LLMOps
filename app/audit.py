from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

AUDIT_LOG_FILE = Path("data/audit.jsonl")


def record_audit_event(
    action: str,
    actor_id: str,
    resource_type: str,
    resource_id: str,
    status: str = "SUCCESS",
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Ghi nhận sự kiện kiểm toán (Audit Event) bảo mật độc lập với application log.
    Schema tiêu chuẩn cho Audit:
    - audit_id: định danh duy nhất của event
    - timestamp: thời điểm UTC ISO 8601
    - actor_id: ai thực hiện (user, admin, system service)
    - action: hành động (e.g., prompt_promoted, prompt_rolled_back, incident_toggled)
    - resource_type: loại tài nguyên (prompt, incident, model_config)
    - resource_id: id tài nguyên
    - status: SUCCESS / FAILED / DENIED
    - details: metadata ngữ cảnh chi tiết
    """
    event = {
        "audit_version": "1.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "actor_id": actor_id,
        "action": action,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "status": status,
        "details": details or {},
    }

    AUDIT_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(AUDIT_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")

    return event
