from django.db.models.signals import post_save
from django.dispatch import receiver

from rest_framework.exceptions import PermissionDenied

from axes.signals import user_locked_out

from .models import CustomUser, CodeVerify


@receiver(post_save, sender=CustomUser)
def create_code_verify(sender, instance, created, *args, **kwargs):
    if created:
        CodeVerify.objects.create(user=instance)
