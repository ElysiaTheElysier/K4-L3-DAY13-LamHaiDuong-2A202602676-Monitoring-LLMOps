# Tài liệu Audit Logging cho LLMOps Platform

> **Bonus Item (+5 điểm):** Hệ thống Audit Log bảo mật độc lập với log ứng dụng thông thường, phục vụ tuân thủ (compliance), truy vết trách nhiệm (accountability) và phát hiện bất thường an ninh.

---

## 1. Schema của Audit Log (`data/audit.jsonl`)

Mỗi bản ghi audit đại diện cho một hành động quản trị hoặc sự kiện bảo mật quan trọng:

```json
{
  "audit_version": "1.0",
  "timestamp": "2026-09-30T04:15:30.123456Z",
  "actor_id": "admin-2A202602676",
  "action": "prompt_rolled_back",
  "resource_type": "prompt",
  "resource_id": "day13-chat",
  "status": "SUCCESS",
  "details": {
    "previous_version": 2,
    "current_version": 1,
    "target_label": "production",
    "reason": "Mitigate latency spike caused by verbose responses",
    "ip_address": "127.0.0.1"
  }
}
```

### Các trường bắt buộc:
* `audit_version`: Phiên bản schema (`1.0`).
* `timestamp`: Thời điểm xảy ra theo chuẩn UTC ISO 8601 (`YYYY-MM-DDTHH:MM:SS.mmmmmmZ`).
* `actor_id`: Mã định danh người/tiến trình thực hiện (ID người dùng băm hoặc tài khoản quản trị).
* `action`: Tên hành động quản trị (`prompt_promoted`, `prompt_rolled_back`, `incident_enabled`, `incident_disabled`, `api_key_rotated`).
* `resource_type`: Loại đối tượng (`prompt`, `incident`, `model_config`, `policy`).
* `resource_id`: Định danh cụ thể của đối tượng (`day13-chat`, `rag_slow`, v.v.).
* `status`: Trạng thái thực thi (`SUCCESS`, `FAILED`, `UNAUTHORIZED`).
* `details`: Từ điển chứa dữ liệu ngữ cảnh (phiên bản trước/sau, lý do thay đổi, địa chỉ IP).

---

## 2. Chính sách lưu trữ và Retention Policy

Để đảm bảo tính toàn vẹn (integrity) và tuân thủ các quy chuẩn bảo mật dữ liệu (SOC 2, ISO 27001):

1. **Tính bất biến (Immutability):**
   - Audit log được ghi theo phương thức **Append-Only**.
   - Khi triển khai production trên cloud, log được stream trực tiếp lên Amazon S3 có bật **Object Lock (Compliance Mode / WORM - Write Once, Read Many)** ngăn chặn việc sửa đổi hoặc xóa kể cả bởi tài khoản root.
2. **Vòng đời lưu trữ (Tiering & Retention):**
   - **Hot Storage (0 – 90 ngày):** Lưu trữ trên Elasticsearch / OpenSearch hoặc file local `data/audit.jsonl` để truy vấn nhanh cho đội ngũ Incident Response và On-call.
   - **Warm / Cold Storage (91 – 365 ngày):** Chuyển sang S3 Standard-IA / Glacier Instant Retrieval để phục vụ kiểm toán định kỳ.
   - **Archival (> 365 ngày):** Tự động purge sau 1 năm hoặc chuyển sang Deep Archive nếu có yêu cầu pháp lý đặc thù.

---

## 3. Các truy vấn minh họa (Example Queries)

### 3.1. Truy vấn bằng `jq` (Command-line)

* **Tìm tất cả các lượt Rollback prompt trong hệ thống:**
  ```bash
  jq 'select(.action == "prompt_rolled_back")' data/audit.jsonl
  ```

* **Kiểm tra ai đã bật/tắt sự cố (incident) gần nhất:**
  ```bash
  jq 'select(.resource_type == "incident") | {timestamp, actor: .actor_id, action, incident: .resource_id, status}' data/audit.jsonl
  ```

* **Thống kê các thao tác quản trị thất bại (`FAILED` hoặc `UNAUTHORIZED`):**
  ```bash
  jq 'select(.status != "SUCCESS")' data/audit.jsonl
  ```

### 3.2. Truy vấn bằng Python

```python
import json
from pathlib import Path

audit_path = Path("data/audit.jsonl")
if audit_path.exists():
    with open(audit_path, "r", encoding="utf-8") as f:
        events = [json.loads(line) for line in f if line.strip()]

    # Lọc các hành động thay đổi prompt
    prompt_changes = [e for e in events if e.get("resource_type") == "prompt"]
    print(f"Tổng số lượt thay đổi prompt: {len(prompt_changes)}")
```
