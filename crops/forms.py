from django import forms
from .models import Crop

class CropForm(forms.ModelForm):
    class Meta:
        model = Crop
        fields = ['crop_name', 'grade', 'price', 'wholesale_price', 'retail_price', 
                  'quantity', 'harvest_date', 'available_until', 'description', 'status', 'image']
        widgets = {
            'harvest_date': forms.DateInput(attrs={'type': 'date'}),
            'available_until': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

