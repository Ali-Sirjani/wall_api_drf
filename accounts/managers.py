from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import BaseUserManager

class UserManager(BaseUserManager):

    def create_user(self, phone, username=''):
        """
        Creates and saves a User with the given username and password.
        """
        user = self.model(
            username=username,
            phone=phone,
        )

        user.set_unusable_password()
        user.save()
        return user

    def create_superuser(self, username, password=None):
        """
        Creates and saves a superuser with the given username and password.
        """
        user = self.create_user(
            username,
        )
        user.set_password(password)
        user.is_admin = True
        user.save(using=self._db)
        return user