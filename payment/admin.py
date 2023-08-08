from django.contrib import admin, messages

from .models import Order, PackageAdToken
from .forms import PackageAdTokenForm


@admin.register(PackageAdToken)
class PackageAdTokenAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'discount', 'discount_price', 'token_quantity', 'datetime_modified',
                    'confirmation', 'is_delete')
    ordering = ('-datetime_modified',)
    list_filter = ('is_delete', 'confirmation')
    search_fields = ('token_quantity', 'name', 'price')
    form = PackageAdTokenForm

    def get_fields(self, request, obj=None):
        fields = ['name', 'description', 'price', 'discount', 'discount_price', 'token_quantity',
                  'confirmation']

        if obj and obj.is_delete:
            fields.extend(['is_delete', 'datetime_deleted'])

        fields.extend(
            ['created_by', 'edited_by', 'confirmed_by', 'unconfirmed_by', 'deleted_by', 'undelete_by']
        )

        return fields

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = ['price', 'datetime_created', 'datetime_modified']

        if not request.user.is_superuser:
            readonly_fields.extend(['confirmation'])
            if obj and obj.is_delete:
                readonly_fields.extend(['is_delete'])

        readonly_fields.extend(
            ['created_by', 'edited_by', 'confirmed_by', 'unconfirmed_by', 'deleted_by', 'undelete_by',
             'datetime_deleted']
        )

        return readonly_fields

    def get_form(self, request, obj=None, change=False, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.request = request
        form.instance = obj
        form.change = change
        return form

    def save_form(self, request, form, change):
        if not change:
            form.instance = self.model.objects.create(**form.cleaned_data)

        return super().save_form(request, form, change)

    def delete_model(self, request, obj):
        if not obj.is_delete:
            obj.soft_delete(request.user)
        else:
            messages.info(request, 'order has was deleted')

    def get_actions(self, request):
        return []
