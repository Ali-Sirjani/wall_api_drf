import random

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from phonenumber_field.modelfields import PhoneNumberField

from .managers import UserManager


class CustomUser(AbstractUser):
    username = models.CharField(blank=True, max_length=100, unique=True, verbose_name=_('username'))
    phone_number = PhoneNumberField(unique=True, region='IR', null=True, verbose_name=_('phone number'))

    objects = UserManager()

    def __str__(self):
        if self.username:
            return self.username
        return str(self.phone_number)

    def get_username(self):
        if self.is_staff or self.is_superuser:
            return self.username
        else:
            return self.phone_number


class CodeVerify(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, verbose_name=_('user'))
    code = models.PositiveIntegerField(default=0, verbose_name=_('code'))
    expiration_timestamp = models.DateTimeField(null=True, blank=True, verbose_name=_('expiration timestamp'))

    def __str__(self):
        return self.user.username

    def create_code(self):
        num = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        self.code = random.choice(num)
        for _ in range(5):
            self.code = (self.code * 10) + random.choice(num)

        self.expiration_timestamp = timezone.now() + timezone.timedelta(minutes=2)
        self.save()

    def get_remaining_time_pass(self):
        time_pass = self.expiration_timestamp - timezone.now()
        if time_pass.seconds < timezone.timedelta(minutes=2).seconds:
            minutes, seconds = divmod(time_pass.seconds, 60)
        else:
            minutes = seconds = 0
        return f'{minutes}:{seconds:02}'

    def is_expired(self):
        return self.expiration_timestamp < timezone.now()
