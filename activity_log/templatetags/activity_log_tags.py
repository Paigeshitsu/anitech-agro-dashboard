"""
Custom template tags for Activity Log.
"""
from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Get item from dictionary by key."""
    if dictionary is None:
        return 0
    return dictionary.get(key, 0)


@register.filter
def get_percentage(value, total):
    """Calculate percentage safely."""
    if total == 0 or total is None:
        return 0
    return round((value / total) * 100, 1)


@register.filter
def getattr_filter(obj, attr):
    """Get attribute from object dynamically."""
    return getattr(obj, attr, '')
