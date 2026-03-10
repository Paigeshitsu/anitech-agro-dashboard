from django.contrib import admin
from .models import MarketPrice, BuyerOffer, ScheduleDistribution

@admin.register(MarketPrice)
class MarketPriceAdmin(admin.ModelAdmin):
    list_display = ('crop_name', 'price', 'date')
    list_filter = ('date',)
    search_fields = ('crop_name',)

@admin.register(BuyerOffer)
class BuyerOfferAdmin(admin.ModelAdmin):
    list_display = ('buyer_name', 'crop_name', 'offer_price', 'status', 'date_offered')
    list_filter = ('status', 'date_offered')
    search_fields = ('buyer_name', 'crop_name')

@admin.register(ScheduleDistribution)
class ScheduleDistributionAdmin(admin.ModelAdmin):
    list_display = ('title', 'scheduled_date')
    list_filter = ('scheduled_date',)
    search_fields = ('title',)
