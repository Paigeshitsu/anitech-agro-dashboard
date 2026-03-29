from django import forms
from .models import Crop

class CropForm(forms.ModelForm):
    class Meta:
        model = Crop
        fields = ['crop_name', 'location', 'season', 'soil_ph', 'rainfall_mm', 
                  'temperature_celsius', 'humidity_percent', 'grade', 'price', 
                  'wholesale_price', 'retail_price', 'quantity', 'harvest_date', 
                  'available_until', 'description', 'status', 'image']
        widgets = {
            'harvest_date': forms.DateInput(attrs={'type': 'date'}),
            'available_until': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make image field optional
        self.fields['image'].required = False
        self.fields['image'].widget.attrs['accept'] = 'image/*'
        # Make environmental data fields optional
        self.fields['location'].required = False
        self.fields['season'].required = False
        self.fields['soil_ph'].required = False
        self.fields['rainfall_mm'].required = False
        self.fields['temperature_celsius'].required = False
        self.fields['humidity_percent'].required = False
        # Make other optional fields not required
        self.fields['grade'].required = False
        self.fields['wholesale_price'].required = False
        self.fields['retail_price'].required = False
        self.fields['description'].required = False
        self.fields['status'].required = False
        # Make date fields optional
        self.fields['harvest_date'].required = False
        self.fields['available_until'].required = False
    
    def clean_harvest_date(self):
        harvest_date = self.cleaned_data.get('harvest_date')
        if not harvest_date:
            return None
        return harvest_date
    
    def clean_available_until(self):
        available_until = self.cleaned_data.get('available_until')
        if not available_until:
            return None
        return available_until

