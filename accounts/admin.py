from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """
    Custom admin for CustomUser model.
    Extends Django's built-in UserAdmin.
    """
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('phone', 'bio', 'is_banned')}),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_banned', 'date_joined')
    list_filter = ('is_staff', 'is_active', 'is_banned', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone')

