from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin


class UserManager(BaseUserManager):

    def create_user(self, username, organization, email, password=None):
        if not username:
            raise ValueError('Username is required.')
        if not email:
            ValueError('Email is required.')

        user = self.model(
            username=username,
            organization=organization,
            email=self.normalize_email(email),
        )

        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, username, email, password, organization=''):
        user = self.create_user(
            username=username,
            organization=organization,
            email=self.normalize_email(email),
            password=password,
        )

        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    username = models.CharField(max_length=40, unique=True)
    organization = models.CharField(max_length=40, blank=True)
    email = models.EmailField(max_length=60, unique=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)
    is_admin = models.BooleanField(default=False, verbose_name='admin')
    is_active = models.BooleanField(default=True, verbose_name='active')
    is_staff = models.BooleanField(default=False, verbose_name='staff')
    is_superuser = models.BooleanField(default=False, verbose_name='super user')

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', ]

    objects = UserManager()

    def __str__(self):
        return self.username

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return True
