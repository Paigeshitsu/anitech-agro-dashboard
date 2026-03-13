from django import forms
from django.forms import TextInput, NumberInput, DateInput, Select, ModelChoiceField, ModelMultipleChoiceField
from .models import MarketPrice, BuyerOffer, SellerOffer, ScheduleDistribution

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
        fields = ['buyer_name', 'contact_number', 'crop_name', 'offer_price', 'quantity', 'expiry_date', 'crop', 'farmer', 'status']
        widgets = {
            'buyer_name': forms.TextInput(attrs={'placeholder': 'Buyer name'}),
            'contact_number': forms.TextInput(attrs={'placeholder': 'Contact number'}),
            'crop_name': forms.TextInput(attrs={'placeholder': 'Crop name'}),
            'offer_price': forms.NumberInput(attrs={'placeholder': 'Offer price per kg', 'step': '0.01'}),
            'quantity': forms.NumberInput(attrs={'placeholder': 'Quantity (kg)', 'step': '0.01'}),
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

class SellerOfferForm(forms.ModelForm):
    class Meta:
        model = SellerOffer
        fields = ['crop', 'ask_price', 'quantity', 'expiry_date', 'status']
        widgets = {
            'ask_price': forms.NumberInput(attrs={'placeholder': 'Ask price per kg', 'step': '0.01'}),
            'quantity': forms.NumberInput(attrs={'placeholder': 'Quantity available (kg)', 'step': '0.01'}),
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
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

class PriceSearchForm(forms.Form):
    search = forms.CharField(
        max_length=100,
        required=False,
        widget=TextInput(attrs={
            'placeholder': 'Search crops (e.g., Rice, Corn)...',
            'class': 'form-control',
        })
    )

