from rest_framework import serializers

from .models import Ad, Category


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('name', )


class AdListSerializer(serializers.ModelSerializer):
    category = CategorySerializer(many=True, required=False, read_only=True)
    author = serializers.ReadOnlyField(source='author.username')

    class Meta:
        model = Ad
        fields = ('id', 'author', 'title', 'image', 'status_product', 'price', 'location',
                  'category', 'slug', 'datetime_modified')

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['status_product'] = instance.get_status_product_display()
        return rep


class AdDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(many=True, required=False, read_only=True)
    author = serializers.ReadOnlyField(source='author.username')

    class Meta:
        model = Ad
        fields = ('id', 'author', 'title', 'text', 'image', 'status_product', 'price',
                  'phone', 'location', 'category', 'sign', 'datetime_modified')

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['status_product'] = instance.get_status_product_display()
        return rep
