from rest_framework import serializers

from phonenumber_field.serializerfields import PhoneNumberField

from .models import Ad, Category, AdReport


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'slug')


class AdListSerializer(serializers.ModelSerializer):
    category = CategorySerializer(many=True, required=False, read_only=True)
    author = serializers.ReadOnlyField(source='author.username')

    class Meta:
        model = Ad
        fields = ('id', 'author', 'title', 'image', 'status_product', 'price', 'location',
                  'category', 'slug', 'datetime_modified')


class SearchSerializer(serializers.Serializer):
    q = serializers.CharField(required=True)


class AdDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(many=True, required=False, read_only=True)
    author = serializers.ReadOnlyField(source='author.username')

    class Meta:
        model = Ad
        fields = ('id', 'author', 'title', 'text', 'image', 'status_product', 'price',
                  'phone', 'location', 'category', 'sign', 'datetime_modified')


class AdReportSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='author.username')
    ad = serializers.ReadOnlyField()

    class Meta:
        model = AdReport
        fields = ('user', 'ad', 'report_reason')


def validate_categorise(categories_inputs, objs_list):
    """
    Validate and retrieve Category objects based on provided identifiers.

    Parameters:
        categories_inputs (list): List of category names or primary keys.
        objs_list (list): List to store retrieved Category objects.

    Raises:
        serializers.ValidationError: If an identifier is not found or is invalid.

    Notes:
        - Assumes 'Category' is a Django model representing categories.
        - Finds 'Category' by name or primary key.
        - Raises validation error if not found or identifier is invalid.
    """
    for identifier in categories_inputs:
        try:
            # Attempt to get the Category object by name
            try:
                category = Category.objects.get(name=identifier)
            except Category.DoesNotExist:
                # If not found by name, try getting it by primary key (pk)
                try:
                    category = Category.objects.get(pk=identifier)
                except Category.DoesNotExist:
                    # If neither name nor pk match, raise a validation error
                    raise serializers.ValidationError(
                        {'category': f'There is no ad with this value ({identifier})'})
        except ValueError:
            # If the identifier is not a valid value (e.g., not string or integer), raise a validation error
            raise serializers.ValidationError({'category': f'Invalid value({identifier}).'})

        objs_list.append(category)


class AdCreateOrUpdateSerializer(serializers.ModelSerializer):
    category = serializers.ListField(child=serializers.CharField(), required=False)
    status_product = serializers.CharField()
    phone = PhoneNumberField(region='IR')

    class Meta:
        model = Ad
        fields = ('title', 'text', 'image', 'status_product', 'price', 'phone',
                  'location', 'category', 'active')

    def validate_status_product(self, value):
        value = value.lower()
        if value in ['need repair', 'worked', 'like new', 'new']:
            return value
        else:
            raise serializers.ValidationError('Invalid status product value.')

    def create(self, validated_data):
        categories_list = []
        try:
            category_values = validated_data.pop('category')
            validate_categorise(category_values, categories_list)
        except KeyError:
            pass

        ad = Ad.objects.create(**validated_data)

        if categories_list:
            ad.category.add(*categories_list)

        return ad

    def update(self, instance, validated_data):
        categories_list = []
        try:
            category_values = validated_data.pop('category')
            validate_categorise(category_values, categories_list)
        except KeyError:
            pass

        instance.category.clear()
        if categories_list:
            instance.category.add(*categories_list)

        # Update specific fields with validated data.
        instance.save(update_fields=validated_data)

        # Set 'confirmation' to False for admin re-check.
        instance.confirmation = False
        instance.save()

        return instance
