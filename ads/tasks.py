from django.utils import timezone
from django.conf import settings

from config.celery import app

from .models import Ad


@app.task
def check_expiration_date_every_day():
    ads = Ad.objects.filter(expiration_date__lt=timezone.now(), is_delete=False)
    ads.update(is_delete=True, delete_with='expired', datetime_deleted=timezone.now())


@app.task
def check_reports_of_ads():
    ads = Ad.objects.filter(count_reports__gte=settings.MIN_REPORTS_TO_BLOCK_AD, is_delete=False)
    ads.update(is_block=True)
