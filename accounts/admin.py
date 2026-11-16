from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    ordering = ('email',)
    list_display = ('email', 'display_name', 'role', 'school', 'is_active')
    list_filter = ('role', 'is_active')
    search_fields = ('email', 'display_name', 'full_name')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Profile', {'fields': ('full_name', 'display_name', 'school', 'profile_photo', 'show_on_leaderboard')}),
        ('Access', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'failed_login_count', 'locked_until')}),
    )
    add_fieldsets = (
        (None, {'classes': ('wide',), 'fields': (
            'email', 'full_name', 'display_name', 'school', 'role', 'password1', 'password2')}),
    )