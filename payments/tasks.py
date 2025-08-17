from celery import shared_task
from django.db import transaction
from django.utils import timezone
from payments.models import WebhookEvent, Payment
from aggregators.factory import get_adapter_class
from schools.models import Student, StudentIdMap, SchoolDirectoryConnection
from school_api.client import SchoolAPIClient

@shared_task(bind=True)
def process_webhook_event_task(self, event_id: int):
    event = (WebhookEvent.objects
             .select_related("aggregator_account", "aggregator_account__school")
             .get(id=event_id))
    adapter = get_adapter_class(event.provider)(event.aggregator_account)
    canonical = adapter.parse_webhook(event.payload)

    # Enrich via School Directory if we don't have a mapping yet
    school = event.aggregator_account.school
    prov_sid = (canonical.get("provider_student_id") or "").strip()
    sch_sid = ""
    student = None

    conn = getattr(school, "directory", None)
    if prov_sid and conn:
        data = SchoolAPIClient(conn).get_by_provider_student_id(prov_sid)
        if data:
            sch_sid = (data.get("school_student_id") or "").strip()
            full_name = (data.get("full_name") or "").strip()
            if sch_sid:
                student, _ = Student.objects.get_or_create(school=school, school_student_id=sch_sid, defaults={"full_name": full_name})
                StudentIdMap.objects.get_or_create(school=school, provider_student_id=prov_sid, defaults={"student": student})

    with transaction.atomic():
        p, created = Payment.objects.select_for_update().get_or_create(
            provider=event.provider,
            external_txn_id=canonical["external_txn_id"],
            defaults={
                "school": school,
                "student": student,
                "provider_student_id": prov_sid,
                "school_student_id": sch_sid,
                "amount": canonical["amount"],
                "currency": canonical["currency"],
                "status": canonical["status"],
                "raw": canonical["raw"],
            },
        )
        if not created:
            p.status = canonical["status"]
            p.amount = canonical["amount"]
            p.currency = canonical["currency"]
            p.raw = canonical["raw"]
            if student and not p.student:
                p.student = student
            if sch_sid and not p.school_student_id:
                p.school_student_id = sch_sid
            p.save(update_fields=["status","amount","currency","raw","student","school_student_id","updated_at"])

        event.processed = True
        event.processed_at = timezone.now()
        event.save(update_fields=["processed", "processed_at"])