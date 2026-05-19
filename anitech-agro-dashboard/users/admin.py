from django.contrib import admin
from .models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'account_type', 'is_verified', 'date_joined')
    list_filter = ('account_type', 'is_verified', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email', 'first_name')
