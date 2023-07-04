import random

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

from phonenumber_field.modelfields import PhoneNumberField


class CustomUser(AbstractUser):
    username = models.CharField(blank=True, verbose_name=_('username'))
    phone = PhoneNumberField(unique=True, region='IR', verbose_name=_('phone'))


class CodeVerify(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, verbose_name=_('user'))
    code = models.PositiveIntegerField(verbose_name=_('code'))

    def save(self, *args, **kwargs):
        num = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        for _ in range(6):
            self.code *= 10 + random.choice(num)
        return super().save(*args, **kwargs)
