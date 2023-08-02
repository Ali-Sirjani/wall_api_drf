from django.utils import timezone

from config.celery import app

from .models import Ad


@app.task
def check_expiration_date_every_day():
    ads = Ad.objects.filter(expiration_date__lt=timezone.now(), is_delete=False)
    ads.update(is_delete=True, delete_with='expired', datetime_deleted=timezone.now())
