import json
from pathlib import Path
from app.audit import record_audit_event, AUDIT_LOG_FILE


def test_record_audit_event(tmp_path: Path, monkeypatch) -> None:
    test_file = tmp_path / "audit_test.jsonl"
    monkeypatch.setattr("app.audit.AUDIT_LOG_FILE", test_file)

    event = record_audit_event(
        action="prompt_rolled_back",
        actor_id="tester",
        resource_type="prompt",
        resource_id="day13-chat",
        status="SUCCESS",
        details={"from_version": 2, "to_version": 1},
    )

    assert event["action"] == "prompt_rolled_back"
    assert event["status"] == "SUCCESS"
    assert test_file.exists()

    lines = test_file.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    saved = json.loads(lines[0])
    assert saved["resource_id"] == "day13-chat"
    assert saved["details"]["to_version"] == 1
