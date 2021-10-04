from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


class UsersAdmin(UserAdmin):
    list_display = ('username', 'organization', 'email', 'date_joined', 'last_login', 'is_admin', 'is_staff')
    search_fields = ('username', 'organization')
    readonly_fields = ('id', 'date_joined', 'last_login')

    filter_horizontal = ()
    list_filter = ()
    fieldsets = ()


admin.site.register(User, UsersAdmin)
