from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

class CustomUserAdmin(UserAdmin):
    # اضافه کردن فیلد role به لیست فیلدهای صفحه ویرایش
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Fields', {'fields': ('role',)}),
    )
    # نمایش فیلد role در لیست کلی کاربران برای دسترسی سریع
    list_display = ('username', 'email', 'role', 'is_staff')

# حالا مدل را با تنظیمات جدید (CustomUserAdmin) ثبت کن
admin.site.register(User, CustomUserAdmin)
