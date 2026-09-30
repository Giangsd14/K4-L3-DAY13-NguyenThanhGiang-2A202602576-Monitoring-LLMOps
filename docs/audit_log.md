# Enterprise Audit Logging & Retention Specification (Bonus +5)

## 1. Overview & Architectural Principles

Our Audit Logging Subsystem tracks administrative changes, incident toggles, prompt updates, and security policies for SOC2/GDPR compliance.

## 2. Audit Event Schema

| Field | Type | Description | Example |
| :--- | :--- | :--- | :--- |
| event_id | UUIDv4 string | Globally unique identifier | 1c4f4952-823d-4878-9183-af1245e1087b |
| timestamp | ISO8601 UTC | Timestamp of action | 2026-09-30T15:40:23.595025+00:00 |
| actor | string | User or service principal | admin, coach@vinuni.edu.vn |
| action | string | Performed action | INCIDENT_ENABLE, INCIDENT_DISABLE, PROMPT_PROMOTE |
| resource | string | Target resource | incident:rag_slow, prompt:day13-chat:v2 |
| status | string | SUCCESS or FAILURE | SUCCESS |
| ip_address | string | Client IP | 127.0.0.1 |
| details | object | JSON metadata diff | {"incident": "rag_slow"} |

## 3. 90-Day Retention Policy & Lifecycle Management

- **0-7 Days (Hot Tier)**: Local JSONL + API access via /api/audit.
- **8-30 Days (Warm Tier)**: Daily gzipped archives synced to cloud object storage (S3/GCS) with Object Lock (WORM).
- **31-90 Days (Cold Tier)**: Transition to S3 Glacier Instant Retrieval / Coldline.
- **91+ Days (Purge Tier)**: Automatic expiration lifecycle rule.

## 4. Querying & Inspection

- REST API: GET /api/audit?limit=10
- CLI analysis: cat data/audit.jsonl | jq .

## 5. Security & Privacy Controls

- Automated PII scrubbing on all metadata payloads.
- Strict RBAC on /api/audit management endpoint.
- Tamper-evident SHA256 audit ledger integration.
