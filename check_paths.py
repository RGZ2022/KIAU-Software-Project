import os
from django.conf import settings
from django.apps import apps

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_faculty.settings')
import django
django.setup()

print("--- مسیرهای جستجوی Template در پروژه شما: ---")
for template_config in settings.TEMPLATES:
    print(f"\nEngine: {template_config['BACKEND']}")
    print(f"Dirs: {template_config['DIRS']}")
    print(f"App Dirs: {template_config['APP_DIRS']}")

print("\n--- اپ‌های نصب شده: ---")
for app_config in apps.get_app_configs():
    print(f"{app_config.name}: {app_config.path}")


