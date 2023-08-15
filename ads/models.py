from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MaxValueValidator, MinValueValidator

from phonenumber_field.modelfields import PhoneNumberField


class Category(models.Model):
    """
        Represents a category for ads.

        The Category class represents a specific category that can be assigned to advertisements.
        Categories provide a way to classify and organize ads based on their nature or purpose.
    """

    name = models.CharField(max_length=300, unique=True, verbose_name='name')
    slug = models.SlugField(allow_unicode=True, blank=True, verbose_name='slug')

    def __str__(self):
        return self.name


class ActiveAdsManger(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(confirmation=True, active=True, is_block=False,
                                             expiration_date__gt=timezone.now(), is_delete=False)


class Ad(models.Model):
    """
        Represents an advertisement.

        The Ads class represents an advertisement posted on a website. It contains various fields
        to store information about the ad, such as the author, category, title, text, price, image,
        and status. Ads can be associated with multiple categories and can be signed by multiple users.
    """

    STATUS_CHOICES = (
        ('need repair', 'Need repair'),
        ('worked', 'Worked'),
        ('like new', 'Like new'),
        ('new', 'New'),
    )

    DELETE_WITH_CHOICES = (
        ('user', 'User'),
        ('staff', 'Staff'),
        ('expired', 'Expired'),
        ('other', 'Other'),
    )

    author = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='ads', verbose_name='author')
    category = models.ManyToManyField(Category, related_name='categories', default=None, blank=True,
                                      verbose_name='category')
    sign = models.ManyToManyField(get_user_model(), related_name='signs', default=None, blank=True, verbose_name='sign')
    title = models.CharField(max_length=200, verbose_name='title')
    text = models.TextField(verbose_name='text')
    price = models.PositiveBigIntegerField(verbose_name='price', validators=(MinValueValidator(10_000),
                                                                             MaxValueValidator(99_999_999_999)))
    image = models.ImageField(upload_to='ad_covers/', verbose_name='image')
    status_product = models.CharField(max_length=30, choices=STATUS_CHOICES, verbose_name='status product')
    location = models.TextField(verbose_name='location')
    phone = PhoneNumberField(region='IR', verbose_name='phone')
    slug = models.SlugField(allow_unicode=True, blank=True, verbose_name='slug')

    # Indicates whether the ad is active or not. Set by the user.
    active = models.BooleanField(default=True, verbose_name='active')

    # Indicates whether the ad has been confirmed by the staff of the site. Set by the staff.
    confirmation = models.BooleanField(default=False, verbose_name='confirmation', help_text='this is for admin')

    is_use_ad_token = models.BooleanField(default=False, blank=True, verbose_name='is use ad token')
    datetime_created = models.DateTimeField(auto_now_add=True, verbose_name='datetime created')
    datetime_modified = models.DateTimeField(auto_now=True, verbose_name='datetime modified')

    # block field
    is_block = models.BooleanField(default=False, blank=True, verbose_name='is block')

    # soft-delete fields
    expiration_date = models.DateTimeField(null=True, verbose_name='expiration date')
    is_delete = models.BooleanField(default=False, verbose_name='is delete')
    delete_with = models.CharField(choices=DELETE_WITH_CHOICES, max_length=15, null=True, blank=True,
                                   verbose_name='delete with')
    datetime_deleted = models.DateTimeField(null=True, blank=True, verbose_name='datetime deleted')

    objects = models.Manager()
    active_objs = ActiveAdsManger()

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.pk:
            self.expiration_date = timezone.now() + timezone.timedelta(minutes=10)

        super().save(*args, **kwargs)

    def soft_delete(self, reason):
        self.datetime_deleted = timezone.now()
        self.delete_with = reason
        self.is_delete = True
        self.save()


class AdReport(models.Model):
    ad = models.ForeignKey(Ad, on_delete=models.CASCADE, related_name='reports')
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='reported_ads')
    report_reason = models.TextField()
    datetime_reported = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['ad', 'user']
