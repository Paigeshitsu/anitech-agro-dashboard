import os, django, json
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'anitech.settings')
django.setup()
from django.test import Client
from django.contrib.auth import get_user_model
User = get_user_model()
c = Client()
user = User.objects.filter(username='testuser').first()
if not user:
    user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass', account_type='buyer')
else:
    user.set_password('testpass')
    user.save()
login_success = c.login(username='testuser', password='testpass')
print('Login success:', login_success)
resp = c.get('/market/')
print('status', resp.status_code)
if resp.status_code == 200:
    content = resp.content.decode('utf-8')
    if 'predictionsData' in content:
        print('SUCCESS: predictionsData found in market page')
        start = content.find('var predictionsData = ')
        if start != -1:
            end = content.find(';', start)
            print('Snippet:', content[start:end+1][:300])
    else:
        print('ISSUE: predictionsData not found in market page')
        print('Response snippet:', content[:1000])
else:
    print('ERROR: status', resp.status_code)
    print('Response:', resp.content.decode('utf-8')[:1000])