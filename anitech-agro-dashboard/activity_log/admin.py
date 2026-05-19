"""
Admin configuration for Activity Log models.
"""
from django.contrib import admin
from .models import ActivityLog, DataRetentionPolicy, LogAggregation


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = [
        'timestamp', 'username', 'event_type', 'severity', 
        'status', 'resource_type', 'resource_name', 'user_ip'
    ]
    list_filter = [
        'event_type', 'severity', 'status', 'resource_type',
        ('timestamp', admin.DateFieldListFilter),
    ]
    search_fields = [
        'username', 'action', 'description', 'resource_name', 
        'user_ip', 'request_path'
    ]
    readonly_fields = [
        'timestamp', 'username', 'user_ip', 'user_agent',
        'request_method', 'request_path', 'request_payload',
        'response_status', 'response_body', 'session_id'
    ]
    ordering = ['-timestamp']
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('timestamp', 'user', 'username', 'event_type', 'action')
        }),
        ('Security & Status', {
            'fields': ('severity', 'status', 'user_ip', 'user_agent')
        }),
        ('Resource Information', {
            'fields': ('resource_type', 'resource_id', 'resource_name')
        }),
        ('Request Details', {
            'fields': ('request_method', 'request_path', 'request_payload'),
            'classes': ('collapse',)
        }),
        ('Response Details', {
            'fields': ('response_status', 'response_body'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('description', 'metadata', 'session_id', 'related_event'),
            'classes': ('collapse',)
        }),
        ('Retention Settings', {
            'fields': ('is_retained', 'retention_until', 'visible_to_roles'),
            'classes': ('collapse',)
        }),
    )


@admin.register(DataRetentionPolicy)
class DataRetentionPolicyAdmin(admin.ModelAdmin):
    list_display = ['name', 'retention_days', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name']


@admin.register(LogAggregation)
class LogAggregationAdmin(admin.ModelAdmin):
    list_display = ['date', 'hour', 'event_type', 'severity', 'count', 'unique_users']
    list_filter = ['event_type', 'severity', 'date']
    ordering = ['-date', '-hour']
