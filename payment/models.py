from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models.functions import Upper
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from django.utils import timezone


class PackageAdToken(models.Model):
    """
    The PackageAdToken model is used to represent a package of advertisement tokens in the system.
    Each package has a unique name and description, price, and quantity of tokens it offers.
    Additionally, it tracks who created, edited, confirmed, and deleted the package, and when these actions took place.
    """
    name = models.CharField(max_length=200, unique=True,
                            verbose_name=_('name'))
    description = models.TextField(unique=True, verbose_name=_('description'))
    price = models.PositiveIntegerField(verbose_name=_('price'))
    discount = models.BooleanField(default=False, verbose_name=_('discount'))
    discount_price = models.PositiveIntegerField(blank=True, null=True, verbose_name=_('discount price'),
                                                 help_text=_(f'price of each ad token is {settings.AD_TOKEN_PRICE}'))
    token_quantity = models.PositiveIntegerField(null=True, verbose_name=_('token quantity'), unique=True,
                                                 validators=(MinValueValidator(1),))

    created_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, related_name='packages_created',
                                   null=True, verbose_name=_('created by'))
    edited_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, related_name='packages_edited',
                                  null=True, verbose_name=_('edited by'))
    confirmed_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, related_name='packages_confirmed',
                                     null=True, verbose_name=_('confirmed by'))
    unconfirmed_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, related_name='packages_unconfirmed',
                                       null=True, verbose_name=_('unconfirmed by'))
    deleted_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, related_name='packages_deleted',
                                   null=True, verbose_name=_('deleted by'))
    undelete_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, related_name='packages_undeleted',
                                    null=True, verbose_name=_('undelete by'))

    datetime_created = models.DateTimeField(auto_now_add=True, null=True, verbose_name=_('datetime created'))
    datetime_modified = models.DateTimeField(null=True, verbose_name=_('datetime modified'))

    confirmation = models.BooleanField(default=False, verbose_name=_('confirmation'), help_text='this is for admin')

    # soft-delete fields
    is_delete = models.BooleanField(default=False, verbose_name=_('is delete'))
    datetime_deleted = models.DateTimeField(null=True, blank=True, verbose_name=_('datetime deleted'))

    class Meta:
        # Constraint to ensure that package names are unique when case is ignored.
        constraints = (
            models.UniqueConstraint(Upper('name'), name='unique name PackageAdToken'),
        )

    def __str__(self):
        return self.name

    def soft_delete(self, user):
        """
        Marks the package as deleted without actually removing it from the database.
        Also sets the user who deleted the package and the time of deletion.
        """
        self.is_delete = True
        self.deleted_by = user
        self.datetime_deleted = timezone.now()
        self.save()
