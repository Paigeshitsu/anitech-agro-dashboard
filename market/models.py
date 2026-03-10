from django.db import models

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
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    date_offered = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Offer for {self.crop_name} by {self.buyer_name}"

class ScheduleDistribution(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    scheduled_date = models.DateTimeField()
    location = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
