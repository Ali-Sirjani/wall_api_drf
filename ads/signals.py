import random

from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.text import slugify

from .models import Category, Ad


@receiver(pre_save, sender=Category)
def create_slug_category(sender, instance, *args, **kwargs):
    if not instance.slug or Category.objects.filter(slug=instance.slug).exclude(pk=instance.pk).exists():
        instance.slug = create_unique_slug(instance, instance.name)


@receiver(pre_save, sender=Ad)
def create_slug_ad(sender, instance, *args, **kwargs):
    if not instance.slug or Ad.objects.filter(slug=instance.slug).exclude(pk=instance.pk).exists():
        instance.slug = create_unique_slug(instance, instance.title)


def create_unique_slug(instance, create_by, slug_primitive=None):
    if slug_primitive is None:
        slug = slugify(create_by, allow_unicode=True)
    else:
        slug = slug_primitive

    ins_class = instance.__class__
    obj = ins_class.objects.filter(slug=slug)

    if obj.exists():
        slug = f'{slug}-{random.choice("1402")}'
        return create_unique_slug(instance, create_by, slug)

    return slug
