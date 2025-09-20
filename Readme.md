# Payment Webhook Integration

This service provides a **generic webhook endpoint** (`/api/webhooks/<provider>`) that accepts payment notifications from multiple providers (e.g. SurePay).
Incoming events are **validated, normalized, persisted, mapped to students**, and **synced to QuickBooks**.

---
## Development Setup

### Prerequisites

- Python 3.11 (or as per `.python-version`)
- Docker and Docker Compose
- Git

### Using Docker (Recommended for Dev)

1. Clone the repository:
   ```bash
   git clone <repo-url>
   cd school-payments
   ```

2. Create and configure the environment file:
   ```bash
   cp .env.example .env  # If .env.example exists, otherwise create .env manually
   ```
   Configure the `.env` file with necessary environment variables (e.g., database credentials, API keys, secrets).

3. Start the services:
   ```bash
   docker-compose -f docker-compsoe-dev.yaml up --build
   ```

   This will start:
   - Web server on http://localhost:8000
   - PostgreSQL database on port 5432
   - Redis on port 6379
   - Celery worker and beat for background tasks

4. Run database migrations (if needed):
   ```bash
   docker-compose -f docker-compsoe-dev.yaml exec web python manage.py migrate
   ```

### Local Setup

1. Install Python using pyenv:
   ```bash
   pyenv install $(cat .python-version)
   pyenv local $(cat .python-version)
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up the database:
   ```bash
   python manage.py migrate
   ```

5. Run the development server:
   ```bash
   python manage.py runserver
   ```

### Testing

Run the test suite:

```bash
pytest -q --disable-warnings -vv
```

Tests cover:
- Signature validation
- Payload schema validation
- Student ID mapping via School Directory API
- Payment creation/upsert
- QuickBooks sync mock

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
SCHOOL_CODE="ng"
WEBHOOK_SECRET="sekret"

PAYLOAD='{
  "event_id": "evt-001",
  "external_txn_id": "txn-123",
  "amount": "100,000",
  "currency": "UGX",
  "status": "SUCCEEDED",
  "provider_student_id": "prov-001"
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



---

## Deployment

This application is deployed to Kubernetes using ArgoCD with separate environments for dev, staging, and production.

### Environments

- **Dev**: Deployed from `dev` branch, single replica, sandbox QBO
- **Staging**: Deployed from `release/*` branches, production QBO settings
- **Prod**: Deployed from `main` branch with semantic version tags (e.g., `v1.0.0`)

### Prerequisites

- AWS EKS cluster
- ArgoCD installed
- ECR repository for Docker images
- External PostgreSQL and Redis services

### CI/CD Pipeline

The GitHub Actions pipeline automatically:
1. Runs tests on pull requests and pushes
2. Builds and pushes Docker images to ECR
3. Updates Kustomize manifests with new image tags
4. Triggers ArgoCD sync for dev and staging

### Manual Production Deployment

For production releases:
1. Create a git tag with semantic versioning: `git tag v1.0.0`
2. Push the tag: `git push origin v1.0.0`
3. Update the ArgoCD application to point to the new tag
4. Manually sync the ArgoCD application

### ArgoCD Applications

Apply the ArgoCD application manifests:
```bash
kubectl apply -f argocd/
```

### Environment Variables

Configure the following secrets in each namespace:
- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: Django secret key
- `QBO_CLIENT_ID` & `QBO_CLIENT_SECRET`: QuickBooks OAuth credentials
- `SCHOOL_API_BASE_URL` & `SCHOOL_API_TOKEN`: School Directory API credentials

### Scaling

- Dev: 1 web replica, 1 worker
- Staging: 2 web replicas, 2 workers
- Prod: 3 web replicas, 3 workers

