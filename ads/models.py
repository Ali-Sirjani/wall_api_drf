from django.db import models
from django.contrib.auth import get_user_model

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


class Ad(models.Model):
    """
        Represents an advertisement.

        The Ads class represents an advertisement posted on a website. It contains various fields
        to store information about the ad, such as the author, category, title, text, price, image,
        and status. Ads can be associated with multiple categories and can be signed by multiple users.
    """

    STATUS_CHOICE = (
        ('0', 'Need repair'),
        ('1', 'Worked'),
        ('2', 'Like new'),
        ('3', 'New'),
    )
    author = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='ads', verbose_name='author')
    category = models.ManyToManyField(Category, related_name='categories', default=None, blank=True,
                                      verbose_name='category')
    sign = models.ManyToManyField(get_user_model(), related_name='signs', default=None, blank=True, verbose_name='sign')
    title = models.CharField(max_length=200, verbose_name='title')
    text = models.TextField(verbose_name='text')
    price = models.CharField(max_length=100, verbose_name='price')
    image = models.ImageField(upload_to='ad_covers/', verbose_name='image')
    status_product = models.CharField(max_length=10, choices=STATUS_CHOICE, verbose_name='status product')
    location = models.TextField(verbose_name='location')
    phone = PhoneNumberField(region='IR', verbose_name='phone')
    slug = models.SlugField(allow_unicode=True, blank=True, verbose_name='slug')

    # Indicates whether the ad is active or not. Set by the user.
    active = models.BooleanField(default=True, verbose_name='active')

    # Indicates whether the ad has been confirmed by the staff of the site. Set by the staff.
    confirmation = models.BooleanField(default=False, verbose_name='confirmation')

    datetime_created = models.DateTimeField(auto_now_add=True, verbose_name='datetime created')
    datetime_modified = models.DateTimeField(auto_now=True, verbose_name='datetime modified')
