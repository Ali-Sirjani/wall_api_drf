from django.contrib.auth.backends import ModelBackend

from .models import CustomUser

import phonenumbers
from phonenumbers import is_valid_number, parse


def validate_ir_phone_number(phone_number):
    try:
        if phone_number[0] == '0':
            phone_number = phone_number[1::]
        try:
            parsed_number = parse(phone_number, "IR")
            if is_valid_number(parsed_number):
                return True
            else:
                return False
        except phonenumbers.NumberParseException:
            return False
    except TypeError:
        return False


class UsernameOrPhoneModelBackend(ModelBackend):
    def authenticate(self, request, **kwargs):
        phone_number = kwargs.get('phone_number')
        if validate_ir_phone_number(phone_number):
            kwargs = {'phone_number': phone_number}
            try:
                user = CustomUser.objects.get(**kwargs)
                return user
            except CustomUser.DoesNotExist:
                return None

        password = kwargs.get('password')
        kwargs = {'username': phone_number}
        try:
            user = CustomUser.objects.get(**kwargs)
            if user.check_password(password) and user.is_staff:
                return user
        except CustomUser.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return CustomUser.objects.get(pk=user_id)
        except CustomUser.DoesNotExist:
            return None


