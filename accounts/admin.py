from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, ActivityType, EmissionFactor, HabitLog


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


@admin.register(ActivityType)
class ActivityTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'category', 'unit', 'max_quantity_per_log', 'max_quantity_per_day', 'is_active')
    list_filter = ('category', 'unit', 'is_active')
    search_fields = ('name', 'code')


@admin.register(EmissionFactor)
class EmissionFactorAdmin(admin.ModelAdmin):
    list_display = ('activity_type', 'co2_saved_per_unit_kg', 'plastic_saved_per_unit_g', 'source_reference', 'effective_from', 'effective_to')
    list_filter = ('activity_type', 'effective_from')
    search_fields = ('activity_type__name', 'source_reference')


@admin.register(HabitLog)
class HabitLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'activity_type', 'quantity', 'log_date', 'co2_saved_kg', 'plastic_saved_g', 'created_at')
    list_filter = ('activity_type', 'log_date')
    search_fields = ('user__display_name', 'user__email', 'notes')
