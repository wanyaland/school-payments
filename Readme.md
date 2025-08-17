# Payment Webhook Integration

This service provides a **generic webhook endpoint** (`/api/webhooks/<provider>`) that accepts payment notifications from multiple providers (e.g. SurePay).
Incoming events are **validated, normalized, persisted, mapped to students**, and **synced to QuickBooks**.

---

## Flow

1. **Provider → Webhook**
   Payment provider (e.g. SurePay) sends signed JSON payload.

2. **Webhook Processing**

   * Verify HMAC signature (`X-Signature`) with the provider’s secret.
   * Match the school using `X-School-Code`.
   * Validate payload schema (Pydantic model).
   * Map `provider_student_id` → `school_student_id` via School Directory API.
   * Create or update `Payment` record.
   * Write `WebhookEvent` audit record.

3. **QuickBooks Sync (Optional)**
   Successful payments are synced to QuickBooks as either:

   * **Invoice Payment** (if student has an open invoice), or
   * **Sales Receipt** (otherwise).

---

## Authentication

All webhook requests **must** include:

| Header          | Value                                                                  |
| --------------- | ---------------------------------------------------------------------- |
| `X-School-Code` | School code configured in AggregatorAccount                            |
| `X-Signature`   | HMAC-SHA256 of raw JSON body, keyed with aggregator’s `webhook_secret` |

---

## Example Payload

```json
{
  "event_id": "evt-001",
  "external_txn_id": "txn-123",
  "amount": "100.50",
  "currency": "UGX",
  "status": "SUCCEEDED",
  "provider_student_id": "prov-001",
  "raw": { "foo": "bar" }
}
```

---

## Example cURL Request

```bash
BASE_URL="http://localhost:8000"
PROVIDER="SUREPAY"
SCHOOL_CODE="SCHEMA-HS"
WEBHOOK_SECRET="sekret"

PAYLOAD='{
  "event_id": "evt-001",
  "external_txn_id": "txn-123",
  "amount": "100.50",
  "currency": "UGX",
  "status": "SUCCEEDED",
  "provider_student_id": "prov-001",
  "raw": {"foo": "bar"}
}'

SIG=$(echo -n "$PAYLOAD" | openssl dgst -sha256 -hmac "$WEBHOOK_SECRET" | cut -d" " -f2)

curl -X POST "$BASE_URL/api/webhooks/$PROVIDER" \
  -H "Content-Type: application/json" \
  -H "X-School-Code: $SCHOOL_CODE" \
  -H "X-Signature: $SIG" \
  -d "$PAYLOAD"
```

---

## Expected Response

```json
{
  "detail": "Webhook accepted",
  "event_id": "evt-001",
  "status": "pending"
}
```

---

## Running Tests

```bash
pytest -q --disable-warnings -vv
```

Tests cover:

* Signature validation
* Payload schema validation
* Student ID mapping via School Directory API
* Payment creation/upsert
* QuickBooks sync mock


