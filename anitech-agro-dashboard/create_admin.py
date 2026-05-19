import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'anitech.settings')
django.setup()

from users.models import User
u, c = User.objects.get_or_create(username='admin', email='admin@anitech.com')
u.set_password('admin123')
u.is_staff = True
u.is_superuser = True
u.account_type = 'admin'
u.save()
print('Admin created:', c)
print('Username: admin')
print('Password: admin123')