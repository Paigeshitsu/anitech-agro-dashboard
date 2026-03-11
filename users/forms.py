from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User

class SignupForm(UserCreationForm):
    ACCOUNT_TYPES = [
        ('admin', 'Admin'),
        ('secretary', 'Secretary'),
        ('farmer', 'Farmer'),
        ('buyer', 'Buyer'),
    ]
    account_type = forms.ChoiceField(choices=ACCOUNT_TYPES, required=True)
    email = forms.EmailField(required=True)
    name = forms.CharField(max_length=100, required=True)

    class Meta:
        model = User
        fields = ('username', 'name', 'email', 'account_type', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['name']
        user.account_type = self.cleaned_data['account_type']
        if commit:
            user.save()
        return user

class LoginForm(AuthenticationForm):
    ACCOUNT_TYPES = [
        ('admin', 'Admin'),
        ('secretary', 'Secretary'),
        ('farmer', 'Farmer'),
        ('buyer', 'Buyer'),
    ]
    account_type = forms.ChoiceField(choices=ACCOUNT_TYPES, required=True)

class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'carrier', 'language', 'profile_picture']
