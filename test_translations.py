import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'anitech.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from crops.views import get_translated_crop_name, CROP_TRANSLATIONS

print("Testing translations:")
print("Rice (en):", get_translated_crop_name('Rice', 'en'))
print("Rice (tl):", get_translated_crop_name('Rice', 'tl'))
print("Test Product (en):", get_translated_crop_name('Test Product', 'en'))
print("Test Product (tl):", get_translated_crop_name('Test Product', 'tl'))
print()
print("CROP_TRANSLATIONS keys:", list(CROP_TRANSLATIONS.keys()))