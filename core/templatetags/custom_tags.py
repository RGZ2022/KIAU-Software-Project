from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(str(key), 0)

@register.filter
def rating_color(value):
    try:
        rating = float(value)
    except:
        return "secondary"  # رنگ خاکستری

    if rating >= 4.0:
        return "success"  # سبز
    elif rating >= 3.0:
        return "warning"  # زرد
    else:
        return "danger"  # قرمز

@register.filter
def star_display(value):
    try:
        rating = float(value)
    except:
        rating = 0

    full = int(rating)
    half = 1 if (rating - full) >= 0.5 else 0
    empty = 5 - full - half

    return "★" * full + "⯪" * half + "☆" * empty
