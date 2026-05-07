- [x] Locate Django settings file that contains STATIC_URL/STATIC_ROOT
- [x] Update anitech/settings.py to ensure STATIC_ROOT uses os.path.join(BASE_DIR, 'staticfiles')
- [x] Ensure settings still reference proper STATIC_DIRS/whitenoise storage
- [x] Run quick Django check (e.g., manage.py check) if available

