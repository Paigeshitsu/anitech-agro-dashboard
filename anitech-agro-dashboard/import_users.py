import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'anitech.settings')
django.setup()

from users.models import User

users_data = [
    {'id': 1, 'name': 'Admin User', 'email': 'admin@anitech.com', 'account_type': 'admin'},
    {'id': 2, 'name': 'Jesus Blancaflor', 'email': 'jesusblancaflor@gmail.com', 'account_type': 'farmer'},
    {'id': 3, 'name': 'Jeremie', 'email': 'jeremie@gmail.com', 'account_type': 'secretary'},
    {'id': 4, 'name': 'Test Farmer', 'email': 'test@test.com', 'account_type': 'farmer'},
    {'id': 5, 'name': 'Test User', 'email': 'test@gmail.com', 'account_type': 'admin'},
    {'id': 6, 'name': 'Test User', 'email': 'testf@gmail.com', 'account_type': 'farmer'},
    {'id': 8, 'name': 'Test Adminssssss', 'email': 'testa@gmail.com', 'account_type': 'admin'},
    {'id': 9, 'name': 'Test Farmer2', 'email': 'testf2@gmail.com', 'account_type': 'farmer'},
    {'id': 10, 'name': 'Test Buyer', 'email': 'testb@gmail.com', 'account_type': 'buyer'},
    {'id': 11, 'name': 'Agri Officer', 'email': 'testo@gmail.com', 'account_type': 'secretary'},
    {'id': 16, 'name': 'Saitama', 'email': 'jaysonreales0@gmail.com', 'account_type': 'farmer'},
]

seen = set()
for data in users_data:
    email = data['email']
    base_username = email.split('@')[0]
    username = base_username
    counter = 1
    while username in seen:
        username = f"{base_username}{counter}"
        counter += 1
    seen.add(username)
    u, created = User.objects.update_or_create(
        id=data['id'],
        defaults={
            'username': username,
            'email': email,
            'account_type': data['account_type'],
            'is_verified': True
        }
    )
    if created:
        u.set_password(username + '123')
        u.save()
        print(f"Created: {username} ({data['account_type']}) - Password: {username}123")
    else:
        print(f"Updated: {username} ({data['account_type']})")