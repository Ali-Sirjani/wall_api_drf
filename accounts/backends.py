from django.contrib.auth.backends import ModelBackend
from django.contrib import messages

from .models import CustomUser

import phonenumbers


def validate_ir_phone_number(phone_number, request):
    if type(phone_number) is str:
        try:
            parsed_number = phonenumbers.parse(phone_number, "IR")
            if phonenumbers.is_valid_number(parsed_number):
                return phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164), True
            else:
                return None, False
        except phonenumbers.NumberParseException:
            return None, False

    if phone_number is not None:
        messages.error(request, 'Type Error')

    return None, False


class UsernameOrPhoneModelBackend(ModelBackend):
    def authenticate(self, request, **kwargs):
        phone_number = kwargs.get('phone_number')
        number, validate = validate_ir_phone_number(phone_number, request)
        if validate:
            user_query_phone = {'phone_number': number}
            try:
                user = CustomUser.objects.get(**user_query_phone)
                return user
            except CustomUser.DoesNotExist:
                return CustomUser.objects.create_user(phone=phone_number)

        password = kwargs.get('password')
        username = kwargs.get('username')
        user_query_username = {'username': username}
        try:
            user = CustomUser.objects.get(**user_query_username)
            if user.check_password(password) and user.is_staff:
                return user
        except CustomUser.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return CustomUser.objects.get(pk=user_id)
        except CustomUser.DoesNotExist:
            return None
