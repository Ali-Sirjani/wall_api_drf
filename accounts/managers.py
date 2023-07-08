from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import BaseUserManager


class UserManager(BaseUserManager):

    def create_user(self, phone=None, username=None):
        """
        Creates and saves a User with the given username and password.
        """

        if not username and not phone:
            raise ValueError("You must provide either a username or a phone number.")

        user = self.model(
            username=username,
            phone_number=phone,
        )

        user.set_unusable_password()
        user.save()
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        """
        Creates and saves a superuser with the given username and password.
        """

        if not username:
            raise ValueError("You must provide either a username.")

        user = self.model(
            username=username,
        )
        user.set_password(password)
        user.is_staff = True
        user.is_superuser = True
        user.is_admin = True
        user.save(using=self._db)
        return user
