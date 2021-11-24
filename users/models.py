from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

CUSTOMER = 1

USER_GROUPS = {
    'Customer': 'C',
    'Driver': 'D',
    'Operator': 'O',
    'Administrator': 'A',
}

USER_GROUPS_CHOICE_FIELDS = [
        (USER_GROUPS['Customer'], 'Customer'),
        (USER_GROUPS['Driver'], 'Driver'),
        (USER_GROUPS['Operator'], 'Operator'),
        (USER_GROUPS['Administrator'], 'Administrator')
    ]

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

        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    username = models.CharField(max_length=40, unique=True)
    organization = models.CharField(max_length=40, blank=True)
    email = models.EmailField(max_length=60, unique=True)
    group = models.CharField(max_length=1, default='C', choices=USER_GROUPS_CHOICE_FIELDS)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', ]

    objects = UserManager()

    def __str__(self):
        return self.username

    def has_module_perms(self, app_label):
        return True
