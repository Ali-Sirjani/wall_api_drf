from django.contrib import admin, messages

from .models import Order, PackageAdToken
from .forms import PackageAdTokenForm, OrderForm


@admin.register(PackageAdToken)
class PackageAdTokenAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'discount_price', 'token_quantity', 'datetime_modified',
                    'confirmation', 'is_delete')
    ordering = ('-datetime_modified',)
    list_filter = ('is_delete', 'confirmation')
    search_fields = ('token_quantity', 'name', 'price')
    form = PackageAdTokenForm

    # Defines the fields to be displayed and editable in the admin panel.
    # The displayed fields 'is_delete' and 'datetime_deleted' depend on the object's status (is_delete).
    def get_fields(self, request, obj=None):
        fields = ['name', 'description', 'price', 'discount', 'discount_price', 'token_quantity',
                  'confirmation']

        if obj:
            if obj.is_delete:
                fields.extend(['is_delete', 'datetime_deleted'])

            fields.extend(
                ['created_by', 'edited_by', 'confirmed_by', 'unconfirmed_by', 'deleted_by', 'undelete_by']
            )

        return fields

    # Defines the fields that should be read-only in the admin panel.
    # Non-superuser users have limited read-only fields.
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

    # Overrides the default form to pass additional context (request, obj, change) to the form.
    # Useful for customizing the form based on the request and instance being edited.
    def get_form(self, request, obj=None, change=False, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.request = request
        form.instance = obj
        return form

    # Overrides the save_form method to handle the creation of new model instances.
    # If the object is new (not changed), it creates a new instance using form data.
    def save_form(self, request, form, change):
        if not change:
            form.instance = self.model.objects.create(**form.cleaned_data)

        return super().save_form(request, form, change)

    # Overrides the delete_model method to handle soft deletion of objects.
    # If the object is not already deleted, it calls the soft_delete method on the model instance.
    # Otherwise, it displays a message indicating that the order has already been deleted.
    def delete_model(self, request, obj):
        if not obj.is_delete:
            obj.soft_delete(request.user)
        else:
            messages.info(request, 'order has was deleted')

    # Overrides the get_actions method to disable all actions in the admin panel for this model.
    # This ensures that no bulk actions can be performed on the records.
    def get_actions(self, request):
        return []


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('customer', 'package', 'completed', 'transaction')
    fieldsets = (
        ('Order info', {
            'fields': ('customer', 'package', 'first_name', 'last_name', 'email', 'phone', 'order_note',
                       'transaction', 'completed', 'datetime_paid'),
        }),
        ('Purchased package info', {
            'fields': ('price', 'discount', 'discount_price', 'token_quantity'),
            'classes': ('collapse',)
        }),
        ('User Actions', {
            'fields': ('created_by', 'completed_by', 'uncompleted_by', 'edited_by'),
        }),
    )
    form = OrderForm
    search_fields = ('transaction', 'phone', 'customer__username')
    list_filter = ('discount', 'completed')

    def get_fieldsets(self, request, obj=None):
        if obj:  # Editing an existing order
            return self.fieldsets
        else:  # Adding a new order
            fieldset = ('Order info', {
                'fields': ('customer', 'package', 'first_name', 'last_name', 'email', 'phone', 'order_note',
                           'completed'),
            }),
            return fieldset

    def has_change_permission(self, request, obj=None):
        # Check if the user has the permission to change the object
        if obj and obj.completed:
            # Only allow users with 'change_completed_order' permission to edit completed orders
            return request.user.has_perm('payment.change_completed_order')
        elif obj and not obj.completed:
            return True

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = ['transaction', 'datetime_ordered', 'datetime_paid', 'completed_by',
                           'uncompleted_by', 'edited_by', 'created_by', 'price', 'discount',
                           'discount_price', 'token_quantity']

        if obj:
            readonly_fields.extend(['customer'])

        if not request.user.has_perm('payment.change_completed_order'):
            readonly_fields.extend(['completed'])

        return readonly_fields

    def get_form(self, request, obj=None, change=False, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.request = request
        form.instance = obj
        return form

    def save_form(self, request, form, change):
        if not change:
            form.instance = self.model.objects.create(**form.cleaned_data)
            
            can_set_package = request.user.has_perm('payment.change_completed_order') and form.cleaned_data
            if can_set_package:
                form.instance.set_package()

        return super().save_form(request, form, change)

    # Overrides the message_user method to prevent showing the success message
    # when deleting an order.
    def message_user(self, request, message, level=messages.INFO, extra_tags='', fail_silently=False):
        if level == messages.SUCCESS and 'deleted successfully' in message:
            message = None

        super().message_user(request, message, level, extra_tags, fail_silently)

    # Overrides the delete_model method to prevent direct deletion of orders.
    # It displays a message indicating that orders cannot be deleted.
    def delete_model(self, request, obj):
        messages.info(request, 'You cannot delete an order.')

    # Overrides the get_actions method to disable all actions in the admin panel for this model.
    # This ensures that no bulk actions can be performed on the records.
    def get_actions(self, request):
        return []
