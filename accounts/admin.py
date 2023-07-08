from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser, CodeVerify
from .forms import CustomUserCreationAdminForm, CustomUserChangeForm


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    form = CustomUserChangeForm
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('phone_number', )}),
    )

    add_form = CustomUserCreationAdminForm
    add_fieldsets = ((None, {'fields': ('username', 'phone_number', 'create_staff', 'password1', 'password2')}), )
    list_display = ('username', 'phone_number', 'email', 'first_name',
                    'last_name', 'is_staff')

    def save_form(self, request, form, change):

        if not change:
            phone_number = form.cleaned_data['phone_number']
            username = form.cleaned_data['username']

            if phone_number:
                if not username:
                    username = phone_number.as_e164

                form.instance = self.model.objects.create_user(
                    phone=phone_number,
                    username=username,
                )
            else:
                password = form.cleaned_data['password1']
                form.instance = self.model.objects.create_superuser(
                    username=username,
                    password=password,
                )
        return super().save_form(request, form, change)


@admin.register(CodeVerify)
class CustomUserAdmin(admin.ModelAdmin):
    pass


