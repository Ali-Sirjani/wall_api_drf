from django.contrib import admin

from .models import Category, Ad


@admin.register(Category)
class AdsAdmin(admin.ModelAdmin):
    pass


@admin.register(Ad)
class AdsAdmin(admin.ModelAdmin):
    fields = ('author', 'title', 'text', 'price', 'image', 'status_product',
              'category', 'location', 'phone', 'active', 'slug', 'confirmation')
    readonly_fields = ('author', )
