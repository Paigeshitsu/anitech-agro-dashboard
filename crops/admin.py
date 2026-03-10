from django.contrib import admin
from .models import Crop

@admin.register(Crop)
class CropAdmin(admin.ModelAdmin):
    list_display = ('crop_name', 'user', 'price', 'quantity', 'status', 'harvest_date')
    list_filter = ('status', 'harvest_date')
    search_fields = ('crop_name', 'user__username')
