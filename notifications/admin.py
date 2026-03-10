from django.contrib import admin
from .models import Notification, ActivityLog, AdminAnnouncement, OTPToken, TranslationCache

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'type', 'is_read', 'created_at')
    list_filter = ('type', 'is_read', 'created_at')
    search_fields = ('title', 'user__username')

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'activity', 'created_at', 'ip_address')
    list_filter = ('activity', 'created_at')
    search_fields = ('user__username', 'activity')

@admin.register(AdminAnnouncement)
class AdminAnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at', 'expiry_date')
    list_filter = ('created_at', 'expiry_date')
    search_fields = ('title',)

@admin.register(OTPToken)
class OTPTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'otp_code', 'expires_at')
    list_filter = ('expires_at',)
    search_fields = ('user__username', 'otp_code')

@admin.register(TranslationCache)
class TranslationCacheAdmin(admin.ModelAdmin):
    list_display = ('source_text', 'source_lang', 'target_lang')
    list_filter = ('source_lang', 'target_lang')
    search_fields = ('source_text',)
