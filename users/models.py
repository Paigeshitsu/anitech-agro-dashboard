from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ACCOUNT_TYPES = [
        ('admin', 'Admin'),
        ('secretary', 'Secretary'),
        ('farmer', 'Farmer'),
        ('buyer', 'Buyer'),
    ]
    account_type = models.CharField(max_length=10, choices=ACCOUNT_TYPES, default='farmer')
    phone = models.CharField(max_length=15, blank=True, null=True)
    carrier = models.CharField(max_length=50, blank=True, null=True)
    is_verified = models.BooleanField(default=True)
    language = models.CharField(max_length=10, default='English')
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)

    def __str__(self):
        return self.username
