from django import template
from anitech.utils import get_crop_name as translate_crop_name

register = template.Library()

@register.filter
def translate_crop(crop_name, lang='en'):
    """Translate crop name to the specified language"""
    return translate_crop_name(crop_name, lang)
