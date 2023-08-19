from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, AuthenticationForm

from phonenumber_field.formfields import PhoneNumberField

from .models import CustomUser, CodeVerify


class CustomUserCreationAdminForm(UserCreationForm):
    phone_number = PhoneNumberField(region='IR', required=False)
    create_staff = forms.BooleanField(required=False)

    class Meta:
        model = CustomUser
        fields = ('phone_number', 'username', 'create_staff')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].required = self.initial.get('create_staff', False)
        self.fields['password2'].required = self.initial.get('create_staff', False)

    def clean(self):
        clean_data = super().clean()
        create_staff = clean_data.get('create_staff')
        password = clean_data.get('password1')

        if create_staff:
            username = clean_data.get('username')
            if not (username and password):
                self.add_error(None, 'When you wanna create a staff user you must fill out username and password!')

            return clean_data

        phone_number = clean_data.get('phone_number')
        if not phone_number or password:
            self.add_error(None, 'do not fill out password field just phone number and username is optional for'
                                 ' create normal user!')

        return clean_data


class CustomAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        del self.fields['username']
        del self.fields['password']

    phone_number = PhoneNumberField(region='IR')


class CustomUserChangeForm(UserChangeForm):
    phone_number = PhoneNumberField(region='IR', required=False)

    class Meta:
        model = CustomUser
        fields = ('phone_number', 'username')


class CodeVerifyForm(forms.ModelForm):
    code = forms.IntegerField()

    class Meta:
        model = CodeVerify
        fields = ('code', )
