from django.db import models
from schools.models import School, Student

class AggregatorAccount(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="aggregator_accounts")
    provider = models.CharField(max_length=50)
    webhook_secret = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    class Meta:
        unique_together = ("school", "provider")

class WebhookEvent(models.Model):
    aggregator_account = models.ForeignKey(AggregatorAccount, on_delete=models.CASCADE, related_name="events")
    provider = models.CharField(max_length=50)
    event_id = models.CharField(max_length=100)
    payload = models.JSONField()
    signature = models.CharField(max_length=255, blank=True, null=True)
    received_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)
    processing_error = models.TextField(blank=True, null=True)
    class Meta:
        unique_together = ("event_id", "aggregator_account")
        indexes = [models.Index(fields=["provider", "event_id"]),]

class Payment(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="payments")
    student = models.ForeignKey(Student, on_delete=models.SET_NULL, null=True, blank=True, related_name="payments")

    provider = models.CharField(max_length=50)
    external_txn_id = models.CharField(max_length=128)
    provider_student_id = models.CharField(max_length=128)
    school_student_id = models.CharField(max_length=64, blank=True, default="")

    amount = models.DecimalField(max_digits=18, decimal_places=2)
    currency = models.CharField(max_length=3)
    status = models.CharField(max_length=20)
    narration = models.CharField(max_length=50, default="Other")
    raw = models.JSONField(default=dict, blank=True)

    # QBO fields (optional, used later)
    qbo_txn_id = models.CharField(max_length=128, null=True, blank=True)
    qbo_txn_type = models.CharField(max_length=64, null=True, blank=True)
    qbo_invoice_id = models.CharField(max_length=64, null=True, blank=True)
    qbo_customer_id = models.CharField(max_length=64, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        unique_together = ("provider", "external_txn_id")
        indexes = [
            models.Index(fields=["school", "created_at"]),
            models.Index(fields=["provider", "external_txn_id"]),
            models.Index(fields=["school", "provider_student_id"]),
        ]