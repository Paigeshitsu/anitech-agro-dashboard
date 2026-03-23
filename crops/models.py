from django.db import models
from users.models import User

class Crop(models.Model):
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('reserved', 'Reserved'),
        ('sold', 'Sold'),
    ]
    
    # Environmental data for ML training
    location = models.CharField(max_length=100, blank=True, null=True, help_text="Region/Province where crop is grown")
    season = models.CharField(max_length=10, blank=True, null=True, choices=[('Wet', 'Wet Season'), ('Dry', 'Dry Season')])
    soil_ph = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True, help_text="Soil pH level (4.0-8.5)")
    rainfall_mm = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, help_text="Average rainfall in mm")
    temperature_celsius = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, help_text="Average temperature in Celsius")
    humidity_percent = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, help_text="Humidity percentage")
    
    # Original fields
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    crop_name = models.CharField(max_length=100)
    grade = models.CharField(max_length=50, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    wholesale_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    retail_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    harvest_date = models.DateField()
    available_until = models.DateField()
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='crops/', blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='available')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.crop_name} by {self.user.first_name}"
