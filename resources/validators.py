import os
from django.core.exceptions import ValidationError

ALLOWED_EXTS = [".pdf", ".ppt", ".pptx", ".doc", ".docx", ".zip"]

def validate_file_extension(file):
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in ALLOWED_EXTS:
        raise ValidationError("فرمت فایل مجاز نیست.")

def validate_file_size(file):
    max_size = 100 * 1024 * 1024  # 100MB
    if file.size > max_size:
        raise ValidationError("حجم فایل بیش از ۱۰۰ مگابایت است.")
