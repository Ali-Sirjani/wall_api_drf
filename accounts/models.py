from django.contrib import messages
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.conf import settings

from django_otp.oath import TOTP
from phonenumber_field.modelfields import PhoneNumberField
import secrets

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

    def last_login_for_month(self):
        result = timezone.timedelta(days=30) <= timezone.now() - self.last_login
        return result


class CodeVerify(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, verbose_name=_('user'))
    code = models.PositiveSmallIntegerField(default=0, verbose_name=_('code'))
    expiration_timestamp = models.DateTimeField(null=True, blank=True, verbose_name=_('expiration timestamp'))

    count_otp = models.PositiveIntegerField(blank=True, default=0, verbose_name=_('count otp'))
    limit_time = models.DateTimeField(null=True, blank=True, verbose_name=_('limit time'))
    # is_limit = models.BooleanField(blank=True, default=False, verbose_name=_('is limit'))

    def __str__(self):
        return self.user.username

    def create_code(self):
        secret_key = secrets.token_hex(16)
        secret_key_byte = secret_key.encode('utf-8')
        totp_obj = TOTP(key=secret_key_byte, digits=7)
        self.code = totp_obj.token()

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

    def send_code(self, request=None):
        if (self.expiration_timestamp is not None) and (self.is_expired()):
            self.create_code()

        if self.count_otp <= settings.MAX_OTP_TRY:
            if settings.MAX_OTP_TRY - self.count_otp == 0:
                self.limit_time = timezone.now() + timezone.timedelta(minutes=1)

            self.count_otp += 1
            self.save()
            return True

        if self.limit_time > timezone.now():
            if request:
                messages.info(request, 'Please after 10 minutes try Again')
            return False

        self.count_otp = 0
        self.save()
        return True

    def code_time_validity(self):
        return (self.expiration_timestamp is None) or (self.is_expired())

    def reset(self):
        self.code = 0
        self.expiration_timestamp = None
        self.count_otp = 0
        self.limit_time = None
        self.save()
