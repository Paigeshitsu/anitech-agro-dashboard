import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'anitech.settings')
django.setup()

from users.models import User
User.objects.all().delete()
print("All users deleted")