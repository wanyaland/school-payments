from django.urls import path
from .views import qbo_authorize, qbo_callback
urlpatterns = [
    path("authorize", qbo_authorize, name="qbo-authorize"),
    path("callback", qbo_callback, name="qbo-callback"),
]