from rest_framework import serializers

from phonenumber_field.serializerfields import PhoneNumberField

from .models import CustomUser, CodeVerify


class UserSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ('username', 'last_login', 'first_name', 'last_name', 'is_active', 'date_joined',
                  'phone_number', 'email', 'ad_token', 'block_time',)

    def get_username(self, obj):
        if obj.phone_number == obj.username:
            return None
        return obj.username


class UpdateUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name')


class LoginSerializer(serializers.ModelSerializer):
    phone_number = PhoneNumberField(region='IR')

    class Meta:
        model = CustomUser
        fields = ('phone_number', )


class CodeVarifySerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField()
    send_again = serializers.BooleanField(required=False)

    class Meta:
        model = CodeVerify
        fields = ('user_id', 'code', 'send_again')
