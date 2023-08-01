from django.db import models
from django.contrib import messages
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.conf import settings

from django_otp.oath import TOTP
from phonenumber_field.modelfields import PhoneNumberField
import secrets

from .managers import UserManager
import ads


class CustomUser(AbstractUser):
    username = models.CharField(blank=True, max_length=100, unique=True, verbose_name=_('username'))
    phone_number = PhoneNumberField(unique=True, region='IR', null=True, verbose_name=_('phone number'))
    email = models.EmailField(blank=True, null=True, unique=True)

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

    def has_free_ad_quota(self):
        # Get the current date
        current_date = timezone.now()
        # Calculate the date 30 days ago
        thirty_days_ago = current_date - timezone.timedelta(days=30)

        # Count the user's ads created within the last 30 days
        ads_within_last_30_days = ads.models.Ad.objects.filter(author=self, datetime_created__gte=thirty_days_ago).count()

        return ads_within_last_30_days < settings.FREE_ADS_MONTHLY_QUOTA


class CodeVerify(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, verbose_name=_('user'))
    code = models.PositiveIntegerField(default=0, verbose_name=_('code'))
    expiration_timestamp = models.DateTimeField(null=True, blank=True, verbose_name=_('expiration timestamp'))

    count_otp = models.PositiveIntegerField(blank=True, default=0, verbose_name=_('count otp'))
    limit_time = models.DateTimeField(null=True, blank=True, verbose_name=_('limit time'))
    # is_limit = models.BooleanField(blank=True, default=False, verbose_name=_('is limit'))

    def __str__(self):
        return self.user.username

    def create_code(self):
        """
        Generates a new verification code and sets the expiration timestamp.

        This method generates a new random verification code using the TOTP algorithm.
        The code is stored in the 'code' attribute of the CodeVerify instance.
        The expiration timestamp is set to the current time plus a duration of 2 minutes.
        The updated CodeVerify instance is saved to the database.
        """
        secret_key = secrets.token_hex(16)
        secret_key_byte = secret_key.encode('utf-8')
        totp_obj = TOTP(key=secret_key_byte, digits=7)
        self.code = totp_obj.token()

        self.expiration_timestamp = timezone.now() + timezone.timedelta(minutes=2)
        self.save()

    def get_remaining_time_pass(self):
        """
        Calculates and returns the remaining time in minutes and seconds until the expiration of the verification code.
        """
        time_pass = self.expiration_timestamp - timezone.now()
        if time_pass.seconds < timezone.timedelta(minutes=2).seconds:
            minutes, seconds = divmod(time_pass.seconds, 60)
        else:
            minutes = seconds = 0
        return f'{minutes}:{seconds:02}'

    def is_expired(self):
        """
        Checks if the verification code has expired.
        """
        return self.expiration_timestamp < timezone.now()

    def send_code(self, request=None):
        """
        Sends the verification code if needed. Generates a new code if the current code has expired.

        Args:
            request: Optional request object. Used to display a message if code sending is limited.

        Returns:
            - True: If the code is sent successfully or the verification limit is not reached.
            - False: If the verification limit is reached and code sending is restricted.
        """
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
        """
        Checks the validity of the verification code's expiration timestamp.
        """
        return (self.expiration_timestamp is None) or (self.is_expired())

    def reset(self):
        """
        Resets the code verification attributes to their initial values.
        """
        self.code = 0
        self.expiration_timestamp = None
        self.count_otp = 0
        self.limit_time = None
        self.save()
