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
    email = models.EmailField(blank=True, null=True, unique=True, verbose_name=_('email'))
    ad_token = models.PositiveIntegerField(blank=True, default=0, verbose_name=_('ad token'))
    token_activated = models.BooleanField(blank=True, default=False, verbose_name=_('token used'))

    count_login = models.PositiveIntegerField(blank=True, default=0, verbose_name=_('count login'))
    block_time = models.DateTimeField(null=True, blank=True, verbose_name=_('block time'))

    objects = UserManager()

    def __str__(self):
        if self.username:
            return self.username
        return str(self.phone_number)

    def get_username(self):
        if self.is_staff or self.is_superuser:
            return self.username
        else:
            return str(self.phone_number)

    def clean(self):
        if not self.email:
            self.email = None

        if not self.phone_number:
            self.phone_number = None

    def can_login(self, login_success=False):
        """
        Determine user's action eligibility based on rate limiting.

        :param: login_success: Whether a successful login has occurred. Default is False.
        :return: True if action is allowed; False if blocked due to rate limiting.
        """
        # Check if there is a recorded last login time for the user
        if self.last_login:
            setting_period_check_login = settings.LOGIN_SUCCESS_CHECK_PERIOD_MINUTE
            reset_time_login = timezone.timedelta(minutes=setting_period_check_login)
            time_since_last_login = timezone.now() - self.last_login

            if login_success:
                # Increment the login attempt counter if a successful login
                self.count_login += 1

            elif reset_time_login < time_since_last_login:
                # Reset counters if enough time has passed since the last login
                self.count_login = 0
                self.block_time = None

            if settings.MAX_LOGIN <= self.count_login:
                setting_block_time = settings.BLOCK_TIME_MAX_LOGIN_MINUTE
                # Apply rate limiting if the maximum allowed login attempts is reached
                self.block_time = timezone.now() + timezone.timedelta(minutes=setting_block_time)

            self.save()

            # Check if the user is currently blocked due to rate limiting
            if self.block_time is None:
                return True

            return False

        # If there is no recorded last login time, allow the login action
        return True

    def last_login_for_month(self):
        result = timezone.timedelta(days=30) <= timezone.now() - self.last_login
        return result

    def has_free_ad_quota(self):
        # Get the current date
        current_date = timezone.now()
        # Calculate the date 30 days ago
        thirty_days_ago = current_date - timezone.timedelta(days=30)

        # Count the user's ads created within the last 30 days
        ads_within_last_30_days = ads.models.Ad.objects.filter(author=self, datetime_created__gte=thirty_days_ago,
                                                               is_use_ad_token=False).count()

        return ads_within_last_30_days < settings.FREE_ADS_MONTHLY_QUOTA

    def try_using_ad_token(self, can_use):
        """
        Use an ad token if 'can_use' is 'True' and tokens are available.

        :param can_use: 'True' if the user intends to use the ad token, 'False' otherwise.
        :return: True if a token was used, False otherwise.
        """
        if self.token_activated:
            return True

        if can_use == 'True' and self.ad_token:
            self.ad_token -= 1
            self.token_activated = True
            self.save()
            return True

        return False


class CodeVerify(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, verbose_name=_('user'))
    code = models.PositiveIntegerField(default=0, verbose_name=_('code'))
    expiration_timestamp = models.DateTimeField(null=True, blank=True, verbose_name=_('expiration timestamp'))

    count_otp = models.PositiveIntegerField(blank=True, default=1, verbose_name=_('count otp'))
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
                setting_limit_time = settings.LIMIT_TIME_MAX_OTP
                self.limit_time = timezone.now() + timezone.timedelta(minutes=setting_limit_time)

            self.count_otp += 1
            self.save()
            return True

        if self.limit_time > timezone.now():
            if request:
                messages.info(request, 'Please after 10 minutes try Again')
            return False

        self.count_otp = 1
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
        self.count_otp = 1
        self.limit_time = None
        self.save()

    def can_start_again(self):
        if self.expiration_timestamp is not None:
            setting_reset_time_otp = settings.RESET_TIME_OTP_MINUTE
            time_reset = self.expiration_timestamp + timezone.timedelta(minutes=setting_reset_time_otp)

            result = time_reset < timezone.now()
            return result

        return False
