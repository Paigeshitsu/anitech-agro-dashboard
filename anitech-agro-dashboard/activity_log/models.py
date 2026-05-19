"""
Activity Log Models for comprehensive audit trail and system event tracking.
"""
from django.db import models
from django.conf import settings
import json


class ActivityLog(models.Model):
    """
    Comprehensive model for tracking all system events, user actions, and administrative changes.
    """
    
    # Event Types
    EVENT_TYPES = [
        ('login', 'User Login'),
        ('logout', 'User Logout'),
        ('create', 'Create Resource'),
        ('read', 'View/Read Resource'),
        ('update', 'Update Resource'),
        ('delete', 'Delete Resource'),
        ('export', 'Export Data'),
        ('import', 'Import Data'),
        ('permission_change', 'Permission Change'),
        ('security_event', 'Security Event'),
        ('system_error', 'System Error'),
        ('api_call', 'API Call'),
        ('configuration_change', 'Configuration Change'),
    ]
    
    # Severity Levels
    SEVERITY_LEVELS = [
        ('info', 'Information'),
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    # Status
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('pending', 'Pending'),
        ('warning', 'Warning'),
    ]
    
    # Resource Types
    RESOURCE_TYPES = [
        ('user', 'User'),
        ('crop', 'Crop'),
        ('market', 'Market'),
        ('notification', 'Notification'),
        ('schedule', 'Schedule'),
        ('inventory', 'Inventory'),
        ('ml_model', 'ML Model'),
        ('system', 'System'),
    ]
    
    # Core Fields
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activity_logs',
        db_index=True
    )
    username = models.CharField(max_length=150, blank=True, db_index=True)
    user_ip = models.GenericIPAddressField(null=True, blank=True, db_index=True)
    user_agent = models.TextField(blank=True, default='')
    
    # Event Details
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES, db_index=True)
    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS, default='info', db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='success', db_index=True)
    
    # Resource Information
    resource_type = models.CharField(max_length=50, choices=RESOURCE_TYPES, blank=True, db_index=True)
    resource_id = models.CharField(max_length=100, blank=True, db_index=True)
    resource_name = models.CharField(max_length=255, blank=True)
    
    # Action Description
    action = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    
    # Additional Metadata
    request_method = models.CharField(max_length=10, blank=True)
    request_path = models.CharField(max_length=500, blank=True)
    request_payload = models.JSONField(null=True, blank=True)
    response_status = models.IntegerField(null=True, blank=True)
    response_body = models.JSONField(null=True, blank=True)
    
    # Related Events
    related_event = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='related_events'
    )
    session_id = models.CharField(max_length=100, blank=True, db_index=True)
    
    # Retention and Visibility
    is_retained = models.BooleanField(default=True)
    retention_until = models.DateTimeField(null=True, blank=True)
    
    # Role-based visibility
    visible_to_roles = models.JSONField(
        default=list,
        blank=True,
        help_text="List of account types that can see this log entry. Empty means visible to all."
    )
    
    # Metadata JSON for extensibility
    metadata = models.JSONField(null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['event_type', '-timestamp']),
            models.Index(fields=['severity', '-timestamp']),
            models.Index(fields=['resource_type', 'resource_id']),
            models.Index(fields=['user_ip', '-timestamp']),
        ]
        verbose_name = 'Activity Log'
        verbose_name_plural = 'Activity Logs'
    
    def __str__(self):
        return f"{self.timestamp} - {self.user} - {self.action}"
    
    def save(self, *args, **kwargs):
        # Auto-populate username if user is set
        if self.user and not self.username:
            self.username = self.user.username
        super().save(*args, **kwargs)
    
    @property
    def icon_class(self):
        """Return icon class based on event type"""
        icons = {
            'login': 'fa-sign-in-alt',
            'logout': 'fa-sign-out-alt',
            'create': 'fa-plus-circle',
            'read': 'fa-eye',
            'update': 'fa-edit',
            'delete': 'fa-trash-alt',
            'export': 'fa-download',
            'import': 'fa-upload',
            'permission_change': 'fa-shield-alt',
            'security_event': 'fa-exclamation-triangle',
            'system_error': 'fa-bug',
            'api_call': 'fa-code',
            'configuration_change': 'fa-cog',
        }
        return icons.get(self.event_type, 'fa-history')
    
    @property
    def severity_color(self):
        """Return color based on severity level"""
        colors = {
            'info': '#17a2b8',      # Blue
            'low': '#6c757d',       # Gray
            'medium': '#ffc107',    # Yellow
            'high': '#fd7e14',      # Orange
            'critical': '#dc3545', # Red
        }
        return colors.get(self.severity, '#6c757d')
    
    @property
    def status_color(self):
        """Return color based on status"""
        colors = {
            'success': '#28a745',   # Green
            'failed': '#dc3545',    # Red
            'pending': '#ffc107',   # Yellow
            'warning': '#fd7e14',   # Orange
        }
        return colors.get(self.status, '#6c757d')
    
    @property
    def is_security_relevant(self):
        """Check if this event is security-relevant"""
        return self.event_type in [
            'login', 'logout', 'permission_change', 'security_event'
        ] or self.severity in ['high', 'critical']
    
    @property
    def is_critical_event(self):
        """Check if this is a critical event"""
        return self.severity == 'critical' or self.status == 'failed'
    
    def get_display_fields(self):
        """Return dictionary of all display fields for export"""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else '',
            'user': self.username,
            'user_ip': self.user_ip or '',
            'event_type': self.get_event_type_display(),
            'severity': self.get_severity_display(),
            'status': self.get_status_display(),
            'resource_type': self.get_resource_type_display() if self.resource_type else '',
            'resource_id': self.resource_id,
            'resource_name': self.resource_name,
            'action': self.action,
            'description': self.description,
            'request_method': self.request_method,
            'request_path': self.request_path,
            'response_status': self.response_status,
        }

    @property
    def display_username(self):
        if self.user:
            full_name = self.user.get_full_name().strip()
            if full_name:
                return full_name
        return self.username or 'System'

    @property
    def role_key(self):
        if self.user and getattr(self.user, 'account_type', None):
            return self.user.account_type
        return (self.metadata or {}).get('account_type', '')

    @property
    def role_label(self):
        role_map = {
            'admin': 'admin',
            'secretary': 'agri-officer',
            'farmer': 'farmer',
            'buyer': 'buyer',
        }
        return role_map.get(self.role_key, 'system' if not self.user else 'user')

    @property
    def module_label(self):
        request_path = (self.request_path or '').lower()
        resource_type = (self.resource_type or '').lower()
        resource_name = (self.resource_name or '').lower()
        action = (self.action or '').lower()

        if 'weather' in request_path or resource_name == 'weather' or 'weather' in action:
            return 'Weather'
        if 'ml' in request_path or 'predict' in request_path or resource_type == 'ml_model':
            return 'AI Prediction'
        if 'auth' in request_path or self.event_type in ['login', 'logout', 'permission_change']:
            return 'Auth'
        if 'crop' in request_path or resource_type == 'crop':
            return 'Crops'
        if 'market' in request_path or resource_type == 'market':
            return 'Offers'
        if 'schedule' in request_path or resource_type == 'schedule':
            return 'Distribution'
        if 'inventory' in request_path or resource_type == 'inventory':
            return 'Inventory'
        if 'notification' in request_path or resource_type == 'notification':
            return 'Notifications'
        if resource_type == 'user':
            return 'Users'
        return 'System'

    @property
    def action_icon_class(self):
        if self.module_label == 'Auth':
            return 'fa-right-to-bracket' if self.event_type == 'login' else 'fa-right-from-bracket'
        if self.module_label == 'Crops':
            return 'fa-seedling'
        if self.module_label == 'Offers':
            return 'fa-cart-shopping'
        if self.module_label == 'Distribution':
            return 'fa-truck'
        if self.module_label == 'Weather':
            return 'fa-cloud'
        if self.module_label == 'AI Prediction':
            return 'fa-brain'
        if self.module_label == 'Inventory':
            return 'fa-boxes-stacked'

        icon_map = {
            'create': 'fa-plus',
            'read': 'fa-eye',
            'update': 'fa-pen',
            'delete': 'fa-trash',
            'export': 'fa-download',
            'import': 'fa-upload',
            'permission_change': 'fa-shield-halved',
            'security_event': 'fa-triangle-exclamation',
            'system_error': 'fa-bug',
            'api_call': 'fa-code',
            'configuration_change': 'fa-sliders',
        }
        return icon_map.get(self.event_type, 'fa-clock-rotate-left')


class DataRetentionPolicy(models.Model):
    """
    Model to define data retention policies for different log types.
    """
    name = models.CharField(max_length=100)
    event_types = models.JSONField(
        default=list,
        help_text="List of event types this policy applies to"
    )
    severity_levels = models.JSONField(
        default=list,
        help_text="List of severity levels this policy applies to"
    )
    retention_days = models.IntegerField(
        default=90,
        help_text="Number of days to retain logs"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Data Retention Policy'
        verbose_name_plural = 'Data Retention Policies'
    
    def __str__(self):
        return f"{self.name} - {self.retention_days} days"


class LogAggregation(models.Model):
    """
    Model to store pre-computed aggregation statistics for activity logs.
    """
    date = models.DateField(db_index=True)
    hour = models.IntegerField(null=True, blank=True)
    event_type = models.CharField(max_length=50, db_index=True)
    severity = models.CharField(max_length=20)
    status = models.CharField(max_length=20)
    resource_type = models.CharField(max_length=50, blank=True)
    count = models.IntegerField(default=0)
    unique_users = models.IntegerField(default=0)
    unique_ips = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-date', '-hour']
        indexes = [
            models.Index(fields=['-date']),
            models.Index(fields=['event_type', '-date']),
        ]
        verbose_name = 'Log Aggregation'
        verbose_name_plural = 'Log Aggregations'
    
    def __str__(self):
        return f"{self.date} - {self.event_type}: {self.count}"
