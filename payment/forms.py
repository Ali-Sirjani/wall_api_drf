from django.forms import ModelForm
from django.contrib import messages
from django.conf import settings

from .models import PackageAdToken


class PackageAdTokenForm(ModelForm):
    class Meta:
        model = PackageAdToken 
        fields = '__all__'
    
    def clean(self):
        # Retrieve the cleaned data
        clean_data = super().clean()
        # Get the current user
        user = self.request.user

        # Check if the package can be edited or created
        can_edit_or_create = not self.instance.is_delete or not clean_data.get('is_delete')

        if can_edit_or_create:
            try:
                # Calculate the price of tokens
                token_quantity = clean_data.get('token_quantity')
                if token_quantity:
                    price_token = settings.AD_TOKEN_PRICE * token_quantity
                else:
                    raise TypeError
            except TypeError:
                # If there's a type error, return the cleaned data as is
                return clean_data

            discount = clean_data.get('discount')
            discount_price = clean_data.get('discount_price')

            # Check if discount is not set but discount price is filled
            if not discount and discount_price:
                self.add_error('discount', 'You must set discount True because you fill out discount price')

            # Check if discount is enabled
            if discount:
                max_discount_percent = settings.MAX_DISCOUNT_PERCENT
                if not 0 < max_discount_percent < 100:
                    # Add an error if the maximum discount percent is out of range
                    self.add_error(None, 'MAX DISCOUNT PERCENT is out of range.'
                                         ' Please report this to the backend developer!')
                    clean_data = {}
                    return clean_data

                # Calculate the minimum discount price based on the maximum discount percent
                min_discount_price = ((100 - max_discount_percent) / 100) * price_token

                # Check discount price conditions
                if price_token and discount_price is None:
                    self.add_error('discount_price', 'You must fill out discount price because you active discount')

                elif price_token <= discount_price:
                    self.add_error('discount_price', 'The amount of the discount price must be less than the price')

                elif discount_price < min_discount_price:
                    self.add_error('discount_price', f'The minimum discount price is {min_discount_price}')

            if self.errors:
                return clean_data

        else:
            # If the package can't be edited or created, display a message and return empty cleaned data
            messages.info(self.request, 'You can not change package until is_delete is True!')
            clean_data = {}
            return clean_data

        print('this is changed_data', self.has_changed())
        # Set the created_by and price fields if the instance is new
        if self.instance.pk is None:
            clean_data['created_by'] = user
            clean_data['price'] = price_token

        elif self.has_changed():
            # Set the edited_by and price fields if the instance already exists
            self.instance.edited_by = user
            self.instance.price = price_token

        # Check if the user is a superuser
        if user.is_superuser:
            if clean_data.get('confirmation'):
                # Set the confirmed_by field if the instance is new
                if self.instance.pk is None:
                    clean_data['confirmed_by'] = user
                else:
                    # Set the confirmed_by field if the instance already exists
                    self.instance.confirmed_by = user

            elif self.instance.confirmation:
                # Set the unconfirmed_by field if the instance has confirmation and in clean data be False
                self.instance.unconfirmed_by = user

            if self.instance.is_delete and not clean_data.get('is_delete'):
                # Set the undelete_by field if the instance is marked for deletion
                # but the is_delete field is not True in clean data
                self.instance.undelete_by = user

        else:
            # If the user is not a superuser, disable confirmation
            self.instance.confirmation = False

        return clean_data
