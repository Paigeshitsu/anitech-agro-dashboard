from django.db import models
from crops.models import Crop
from users.models import User
from django.conf import settings

class Inventory(models.Model):
    ITEM_TYPES = [
        ('seed', 'Seeds'), 
        ('fert', 'Fertilizer'), 
        ('tool', 'Tools'),
        ('other', 'Other')
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='inventory_items', null=True, blank=True)
    item_name = models.CharField(max_length=100)
    item_type = models.CharField(max_length=10, choices=ITEM_TYPES, default='other')
    quantity = models.IntegerField()
    unit = models.CharField(max_length=20, default="pcs")
    date_added = models.DateTimeField(auto_now_add=True)
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
        if self.crop.quantity >= self.quantity_sold:
            self.crop.quantity -= self.quantity_sold
            if self.crop.quantity <= 0:
                self.crop.status = 'sold'
                self.crop.quantity = 0
            self.crop.save()
        else:
            # Not enough quantity - raise an error or handle gracefully
            from django.core.exceptions import ValidationError
            raise ValidationError(f"Not enough crop quantity. Available: {self.crop.quantity}")
        super().save(*args, **kwargs)

class MarketPrice(models.Model):
    crop_name = models.CharField(max_length=100)
    current_price = models.DecimalField(max_digits=10, decimal_places=2)
    previous_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    unit = models.CharField(max_length=20, default='per kg')
    last_updated = models.DateTimeField(auto_now=True)
    date = models.DateField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=['crop_name']), models.Index(fields=['-last_updated'])]

    def save(self, *args, **kwargs):
        # Track previous price before updating
        if self.pk:
            try:
                old_instance = MarketPrice.objects.get(pk=self.pk)
                if self.previous_price is None:
                    self.previous_price = old_instance.current_price
            except MarketPrice.DoesNotExist:
                pass
        super().save(*args, **kwargs)

    @property
    def trend_percent(self):
        if self.previous_price and self.previous_price > 0:
            return ((self.current_price - self.previous_price) / self.previous_price) * 100
        return 0

    def __str__(self):
        return f"{self.crop_name} - {self.current_price} {self.unit}"

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

    @property
    def get_total_value(self):
        return float(self.ask_price) * float(self.quantity)

class ScheduleDistribution(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]
    title = models.CharField(max_length=255)
    description = models.TextField()
    quantity = models.CharField(max_length=100, blank=True, null=True, help_text="e.g., 100 sacks, 500 kg")
    recipient = models.CharField(max_length=255, blank=True, null=True, help_text="Name of the recipient")
    scheduled_date = models.DateTimeField()
    location = models.CharField(max_length=255)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

