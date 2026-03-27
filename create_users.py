import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'anitech.settings')
django.setup()

from users.models import User

# Delete existing users if they exist
User.objects.filter(username='admin').delete()
User.objects.filter(username='secretary').delete()
User.objects.filter(username='buyer').delete()
User.objects.filter(username='farmer').delete()

# Create users
admin = User.objects.create_user('admin', 'admin@anitech.com', 'admin123', account_type='admin')
sec = User.objects.create_user('secretary', 'secretary@anitech.com', 'secretary123', account_type='secretary')
buyer = User.objects.create_user('buyer', 'buyer@anitech.com', 'buyer123', account_type='buyer')
farmer = User.objects.create_user('farmer', 'farmer@anitech.com', 'farmer123', account_type='farmer')

print('Users created successfully!')
print('='*40)
print('Admin:     admin / admin123')
print('Secretary: secretary / secretary123')
print('Buyer:     buyer / buyer123')
print('Farmer:    farmer / farmer123')
print('='*40)
