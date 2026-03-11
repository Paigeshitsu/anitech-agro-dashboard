from django import forms
from .models import MarketPrice, BuyerOffer, ScheduleDistribution

class MarketPriceForm(forms.ModelForm):
    class Meta:
        model = MarketPrice
        fields = ['crop_name', 'price']
        widgets = {
            'crop_name': forms.TextInput(attrs={'placeholder': 'e.g., Rice, Corn, Vegetables'}),
            'price': forms.NumberInput(attrs={'placeholder': 'Price per kg', 'step': '0.01'}),
        }

class BuyerOfferForm(forms.ModelForm):
    class Meta:
        model = BuyerOffer
        fields = ['buyer_name', 'contact_number', 'crop_name', 'offer_price', 'status']
        widgets = {
            'buyer_name': forms.TextInput(attrs={'placeholder': 'Buyer name'}),
            'contact_number': forms.TextInput(attrs={'placeholder': 'Contact number'}),
            'crop_name': forms.TextInput(attrs={'placeholder': 'Crop name'}),
            'offer_price': forms.NumberInput(attrs={'placeholder': 'Offer price', 'step': '0.01'}),
        }

class ScheduleDistributionForm(forms.ModelForm):
    class Meta:
        model = ScheduleDistribution
        fields = ['title', 'description', 'scheduled_date', 'location', 'status']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'e.g., Rice Distribution'}),
            'description': forms.Textarea(attrs={'placeholder': 'Description of the schedule', 'rows': 3}),
            'scheduled_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'location': forms.TextInput(attrs={'placeholder': 'e.g., Distribution Center A'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

