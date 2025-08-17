import json
from django.db import transaction
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from pydantic import ValidationError

from payments.models import AggregatorAccount, WebhookEvent
from aggregators.factory import get_adapter_class
from webhooks.validators import get_signature_header, get_timestamp_header, verify_hmac_with_timestamp
from payments.tasks import process_webhook_event_task

@api_view(["POST"])  
@permission_classes([AllowAny])
def payment_webhook(request, provider: str):
    try:
        body = request.body
        payload = json.loads(body.decode("utf-8"))
    except Exception:
        return Response({"detail":"invalid json"}, status=status.HTTP_400_BAD_REQUEST)

    school_code = request.headers.get("X-School-Code")
    if not school_code:
        return Response({"detail":"missing school"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        account = (AggregatorAccount.objects.select_related("school")
                   .get(school__code=school_code, provider=provider.upper(), is_active=True))
    except AggregatorAccount.DoesNotExist:
        return Response({"detail":f"no active {provider} account"}, status=status.HTTP_404_NOT_FOUND)

    sig = get_signature_header(request)
    ts  = get_timestamp_header(request)
    if not verify_hmac_with_timestamp(account.webhook_secret or "", body, sig, ts):
        return Response({"detail":"signature/timestamp invalid"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        adapter = get_adapter_class(account.provider)(account)
        canonical = adapter.parse_webhook(payload)
    except ValidationError as ve:
        return Response({"detail": f"schema invalid: {ve.errors()}"}, status=status.HTTP_400_BAD_REQUEST)
    if not (canonical.get("provider_student_id") or "").strip():
        return Response({"detail":"provider_student_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    with transaction.atomic():
        event, created = WebhookEvent.objects.get_or_create(
            aggregator_account=account,
            event_id=canonical["event_id"],
            defaults={"provider": account.provider, "payload": payload, "signature": sig},
        )
        if not created and event.processed:
            return Response({"status":"ok", "idempotent": True})

    process_webhook_event_task.delay(event_id=event.id)
    return Response({"status":"ok"})