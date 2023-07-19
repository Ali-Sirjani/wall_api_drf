from rest_framework import serializers

from phonenumber_field.serializerfields import PhoneNumberField

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


class AdCreateSerializer(serializers.ModelSerializer):
    category = serializers.ListField(child=serializers.CharField(), required=False)
    status_product = serializers.CharField()
    phone = PhoneNumberField(region='IR')

    class Meta:
        model = Ad
        exclude = ('id', 'author', 'sign', 'slug', 'confirmation', 'datetime_created', 'datetime_modified')

    def validate_status_product(self, value):
        if value in ['Need repair', 'need repair', '0']:
            value = '0'

        elif value in ['Worked', 'worked', '1']:
            value = '1'

        elif value in ['Like new', 'like new', '2']:
            value = '2'

        elif value in ['New', 'new', '3']:
            value = '3'

        else:
            raise serializers.ValidationError('Invalid status product value.')

        return value

    def create(self, validated_data):
        category_list = []
        try:
            category_values = validated_data.pop('category')
            for identifier in category_values:
                try:
                    try:
                        category = Category.objects.get(name=identifier)
                    except Category.DoesNotExist:
                        try:
                            category = Category.objects.get(pk=identifier)
                        except Category.DoesNotExist:
                            raise serializers.ValidationError(
                                {'error': f'There is no ad with this value ({identifier})'})
                except ValueError:
                    raise serializers.ValidationError({'error': f'Invalid value({identifier}).'})

                category_list.append(category)

        except KeyError:
            pass

        ad = Ad.objects.create(**validated_data)

        if category_list:
            ad.category.add(*category_list)

        return ad
