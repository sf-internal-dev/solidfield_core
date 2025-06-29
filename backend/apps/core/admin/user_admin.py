from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from backend.apps.core.models import AccountHolderUser

@admin.register(AccountHolderUser)
class AccountHolderUserAdmin(BaseUserAdmin):
    model = AccountHolderUser
    ordering = ['-created_at']
    list_display = ['email', 'full_name', 'is_active', 'is_staff', 'tenant', 'created_at']
    list_filter = ['is_active', 'is_staff', 'tenant']
    search_fields = ['email', 'full_name']

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('full_name',)}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Tenant Info'), {'fields': ('tenant',)}),
        (_('Important dates'), {'fields': ('last_login', 'created_at')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'full_name', 'password1', 'password2', 'tenant', 'is_active', 'is_staff'),
        }),
    )

    readonly_fields = ['created_at']
