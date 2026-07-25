from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

class CustomUserAdmin(UserAdmin):
    # Role field
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Fields', {'fields': ('role',)}),
    )

    # User list
    list_display = ('username', 'email', 'role', 'is_staff')

# Register
admin.site.register(User, CustomUserAdmin)
