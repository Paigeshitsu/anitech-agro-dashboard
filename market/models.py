from django.db import models
from crops.models import Crop
from users.models import User
from django.conf import settings

class Inventory(models.Model):
    ITEM_TYPES = [('seed', 'Seeds'), ('fert', 'Fertilizer'), ('tool', 'Tools')]
    item_name = models.CharField(max_length=100)
    item_type = models.CharField(max_length=10, choices=ITEM_TYPES)
    quantity = models.IntegerField()
    unit = models.CharField(max_length=20, default="kg")
    last_restocked = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.item_name} ({self.quantity} {self.unit})"

class SaleRecord(models.Model):
    """The 'Receipt' logic from the PHP system"""
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE)
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    quantity_sold = models.DecimalField(max_digits=10, decimal_places=2)
    sale_date = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Business Logic: Deduct from Crop quantity when sold
        self.crop.quantity -= self.quantity_sold
        if self.crop.quantity <= 0:
            self.crop.status = 'sold'
        self.crop.save()
        super().save(*args, **kwargs)

class MarketPrice(models.Model):
    crop_name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.crop_name} - {self.price}"

class BuyerOffer(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Accepted', 'Accepted'),
        ('Rejected', 'Rejected'),
    ]
    buyer_name = models.CharField(max_length=100)
    contact_number = models.CharField(max_length=50, blank=True, null=True)
    crop_name = models.CharField(max_length=100)
    offer_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    expiry_date = models.DateField(null=True, blank=True)
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE, null=True)
    farmer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_offers', null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    date_offered = models.DateField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['-date_offered']),
            models.Index(fields=['status']),
            models.Index(fields=['crop']),
            models.Index(fields=['farmer']),
        ]

    def __str__(self):
        return f"Offer for {self.crop_name} by {self.buyer_name}"

class SellerOffer(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Accepted', 'Accepted'),
        ('Rejected', 'Rejected'),
    ]
    farmer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posted_offers')
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE)
    ask_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    expiry_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    date_posted = models.DateField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['-date_posted']),
            models.Index(fields=['status']),
            models.Index(fields=['crop']),
        ]

    def __str__(self):
        return f"Sell {self.crop.crop_name} by {self.farmer.username} @ {self.ask_price}"

class ScheduleDistribution(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]
    title = models.CharField(max_length=255)
    description = models.TextField()
    scheduled_date = models.DateTimeField()
    location = models.CharField(max_length=255)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

