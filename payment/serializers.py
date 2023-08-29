from rest_framework import serializers

from phonenumber_field.serializerfields import PhoneNumberField

from .models import PackageAdToken, Order


class PackageAdTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = PackageAdToken
        fields = ('pk', 'name', 'description', 'price', 'discount', 'discount_price', 'token_quantity')
        read_only_fields = fields


class OrderCreateOrUpdateSerializer(serializers.ModelSerializer):
    phone = PhoneNumberField(region='IR')

    class Meta:
        model = Order
        fields = ('package', 'first_name', 'last_name', 'email', 'phone', 'order_note')

        extra_kwargs = {
            'package': {'required': True, 'allow_null': False},
            'first_name': {'required': True, 'allow_null': False},
            'last_name': {'required': True, 'allow_null': False},
            'phone': {'required': True, 'allow_null': False},
        }

    def validate_package(self, value):
        if value.is_delete or not value.confirmation:
            raise serializers.ValidationError('Invalid package value.')

        return value


class OrderReadSerializer(serializers.ModelSerializer):
    package = PackageAdTokenSerializer()

    class Meta:
        model = Order
        fields = ('pk', 'package', 'first_name', 'last_name', 'email', 'phone', 'order_note',
                  'transaction', 'price', 'discount', 'discount_price', 'token_quantity')
        read_only_fields = fields

    def to_representation(self, instance):
        # Get the default serialized data
        data = super().to_representation(instance)

        if data['price'] is None:
            del data['price'], data['discount'], data['discount_price'], data['token_quantity']

        return data
