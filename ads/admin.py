from django.contrib import admin
from django.contrib import messages

from .models import Category, Ad, AdReport
from .forms import AdForm


@admin.register(Category)
class AdsAdmin(admin.ModelAdmin):
    pass


class AdReportTabu(admin.TabularInline):
    model = AdReport
    fields = ('user', 'report_reason', 'datetime_reported')
    readonly_fields = fields
    ordering = ('-datetime_reported', )
    max_num = 0


@admin.register(Ad)
class AdsAdmin(admin.ModelAdmin):
    list_display = ('title', 'price', 'active', 'confirmation', 'datetime_modified', 'expiration_date', 'is_delete')
    ordering = ('-datetime_modified', )
    list_filter = ('active', 'is_delete', 'is_block', 'is_use_ad_token')
    actions = ('soft_delete_selected', )
    inlines = (AdReportTabu, )
    form = AdForm

    def get_fields(self, request, obj=None):
        fields = ['author', 'title', 'text', 'price', 'image', 'status_product', 'category',
                  'location', 'phone', 'active', 'is_use_ad_token', 'count_reports', 'slug', 'confirmation',
                  'datetime_modified', 'expiration_date']

        if obj:

            if obj.is_block:
                fields.append('is_block')

            if obj.is_delete:
                fields.extend(['is_delete', 'delete_with', 'datetime_deleted'])

        return fields

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = ['datetime_modified', 'expiration_date', 'datetime_deleted']

        if obj:
            readonly_fields.append('author')

        return readonly_fields

    def save_model(self, request, obj, form, change):
        if change:
            if not obj.is_block and 'is_block' in form.changed_data:
                obj.reports.filter(investigated=False).update(investigated=True)
                obj.count_reports = 0

        return super().save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        if not obj.is_delete:
            obj.soft_delete('staff')
        else:
            messages.info(request, 'Ad has was deleted')

    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def soft_delete_selected(self, request, queryset):
        # Perform the soft deletion for selected objects
        for obj in queryset:
            obj.soft_delete(reason='staff')

    soft_delete_selected.short_description = 'Soft delete selected objects'
