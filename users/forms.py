from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User

class SignupForm(UserCreationForm):
    ACCOUNT_TYPES = [
        ('farmer', 'Farmer'),
        ('buyer', 'Buyer'),
    ]
    account_type = forms.ChoiceField(choices=ACCOUNT_TYPES, required=True, widget=forms.Select(attrs={
        'class': 'form-control',
    }))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your email'
    }))
    name = forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your full name'
    }))
    phone = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your contact number'
    }))

    class Meta:
        model = User
        fields = ('username', 'name', 'phone', 'email', 'account_type', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Choose a username'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Create password'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirm password'})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['name']
        user.phone = self.cleaned_data.get('phone', '')
        user.account_type = self.cleaned_data['account_type']
        if commit:
            user.save()
        return user

class LoginForm(AuthenticationForm):
    ACCOUNT_TYPES = [
        ('', 'Select your role'),
        ('admin', 'Admin'),
        ('secretary', 'Secretary'),
        ('farmer', 'Farmer'),
        ('buyer', 'Buyer'),
    ]
    account_type = forms.ChoiceField(choices=ACCOUNT_TYPES, required=True, widget=forms.Select(attrs={
        'class': 'form-control',
        'required': 'required'
    }))
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Enter your username'})
        self.fields['password'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Enter your password'})

class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'carrier', 'language', 'profile_picture']
