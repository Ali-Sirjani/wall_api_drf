from rest_framework import serializers

from .models import PackageAdToken, Order


class PackageAdTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = PackageAdToken
        fields = ('pk', 'name', 'description', 'price', 'discount', 'discount_price', 'token_quantity')
        read_only_fields = fields
