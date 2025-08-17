# config/celery.py
import os
from celery import Celery

# Make sure Django settings are loaded when Celery starts
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("config")

# Read settings with CELERY_ prefix from Django settings.py
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks.py in installed apps
app.autodiscover_tasks()
