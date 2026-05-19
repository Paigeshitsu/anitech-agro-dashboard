from django import forms
from django.forms import TextInput, NumberInput, DateInput, Select, ModelChoiceField, ModelMultipleChoiceField
from .models import MarketPrice, BuyerOffer, SellerOffer, ScheduleDistribution

class MarketPriceForm(forms.ModelForm):
    class Meta:
        model = MarketPrice
        fields = ['crop_name', 'current_price', 'previous_price', 'unit']
        widgets = {
            'crop_name': forms.TextInput(attrs={'placeholder': 'e.g., Rice, Corn, Vegetables'}),
            'current_price': forms.NumberInput(attrs={'placeholder': 'Current price per unit', 'step': '0.01'}),
            'previous_price': forms.NumberInput(attrs={'placeholder': 'Previous price (optional)', 'step': '0.01'}),
            'unit': forms.TextInput(attrs={'placeholder': 'e.g., per kg'}),
        }

class BuyerOfferForm(forms.ModelForm):
    quantity = forms.DecimalField(
        min_value=1,
        max_value=9999,
        decimal_places=2,
        max_digits=10,
        widget=forms.NumberInput(attrs={
            'placeholder': 'Quantity (kg)',
            'step': '0.01',
            'min': '1',
            'max': '9999',
        }),
        error_messages={
            'min_value': 'Quantity must be at least 1 kg.',
            'max_value': 'Quantity cannot exceed 9999 kg.',
        },
    )

    class Meta:
        model = BuyerOffer
        fields = ['contact_number', 'crop_name', 'offer_price', 'quantity', 'expiry_date', 'crop', 'farmer']
        widgets = {
            'contact_number': forms.TextInput(attrs={'placeholder': 'Contact number'}),
            'crop_name': forms.TextInput(attrs={'placeholder': 'Crop name'}),
            'offer_price': forms.NumberInput(attrs={'placeholder': 'Offer price per kg', 'step': '0.01'}),
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hide crop and farmer from regular users - they'll be set in the view
        self.fields['crop'].required = False
        self.fields['farmer'].required = False

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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['description'].required = False

    class Meta:
        model = ScheduleDistribution
        fields = ['title', 'description', 'quantity', 'recipient', 'scheduled_date', 'location', 'status']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'e.g., Rice Distribution'}),
            'description': forms.Textarea(attrs={'placeholder': 'Description of the schedule', 'rows': 3}),
            'quantity': forms.TextInput(attrs={'placeholder': 'e.g., 100 sacks, 500 kg'}),
            'recipient': forms.TextInput(attrs={'placeholder': 'Name of the recipient'}),
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

