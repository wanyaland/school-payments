from django.urls import path
from .views import payment_webhook

urlpatterns = [
    path("<str:provider>", payment_webhook, name="payment-webhook"),
]