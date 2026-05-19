"""
Utility functions for Activity Log management.
"""
import re
from difflib import SequenceMatcher
from django.db.models import Q


def get_client_ip(request):
    """
    Extract client IP address from request.
    Handles X-Forwarded-For header for proxied requests.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def fuzzy_search(queryset, search_term, threshold=0.4):
    """
    Perform fuzzy search across multiple fields.
    Uses similarity matching to find relevant results.
    """
    if not search_term:
        return queryset
    
    search_term_lower = search_term.lower()
    
    # Get all logs that might match
    search_fields = [
        'username', 'action', 'description', 'resource_name',
        'user_ip', 'request_path', 'request_method'
    ]
    
    # First, do exact/contains search
    q_filter = Q()
    for field in search_fields:
        q_filter |= Q(**{f'{field}__icontains': search_term})
    
    initial_results = queryset.filter(q_filter)
    
    # If we have exact matches, return them
    if initial_results.exists():
        return initial_results
    
    # Otherwise, perform fuzzy matching
    results = []
    for log in queryset[:1000]:  # Limit to first 1000 for performance
        max_similarity = 0
        for field in search_fields:
            value = getattr(log, field, '') or ''
            if isinstance(value, str):
                similarity = SequenceMatcher(
                    None, 
                    search_term_lower, 
                    value.lower()
                ).ratio()
                max_similarity = max(max_similarity, similarity)
        
        if max_similarity >= threshold:
            results.append(log.id)
    
    return queryset.filter(id__in=results)


def log_activity(
    request=None,
    user=None,
    event_type='system',
    severity='info',
    status='success',
    action='',
    description='',
    resource_type='',
    resource_id='',
    resource_name='',
    request_payload=None,
    response_status=None,
    response_body=None,
    metadata=None,
    visible_to_roles=None
):
    """
    Helper function to create activity log entries.
    Can be used from views, signals, or anywhere in the code.
    """
    from .models import ActivityLog
    
    # Get user from request if not provided
    if user is None and request is not None:
        user = getattr(request, 'user', None)
    
    # Get IP address
    user_ip = None
    if request:
        user_ip = get_client_ip(request)
    
    # Get username
    username = ''
    if user and user.is_authenticated:
        username = user.username
    elif request and hasattr(request, 'user') and request.user.is_authenticated:
        username = request.user.username
    
    # Create the log entry
    log = ActivityLog.objects.create(
        user=user,
        username=username,
        user_ip=user_ip,
        user_agent=request.META.get('HTTP_USER_AGENT', '') if request else '',
        event_type=event_type,
        severity=severity,
        status=status,
        resource_type=resource_type,
        resource_id=resource_id,
        resource_name=resource_name,
        action=action,
        description=description,
        request_method=request.method if request else '',
        request_path=request.path if request else '',
        request_payload=request_payload,
        response_status=response_status,
        response_body=response_body,
        metadata=metadata or {},
        visible_to_roles=visible_to_roles or [],
    )
    
    return log


def log_security_event(request, event_type, severity, action, description, resource_type=None, resource_id=None):
    """
    Specialized function for logging security-related events.
    Automatically sets higher severity for security events.
    """
    from .models import ActivityLog
    
    user = getattr(request, 'user', None)
    user_ip = get_client_ip(request)
    username = user.username if user and user.is_authenticated else 'anonymous'
    
    # Security events should at least be 'medium' severity
    if severity not in ['high', 'critical']:
        severity = 'medium'
    
    # Only visible to admin by default
    visible_to_roles = ['admin']
    
    return ActivityLog.objects.create(
        user=user,
        username=username,
        user_ip=user_ip,
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        event_type=event_type,
        severity=severity,
        status='success',
        resource_type=resource_type or 'security',
        resource_id=resource_id or '',
        action=action,
        description=description,
        request_method=request.method,
        request_path=request.path,
        visible_to_roles=visible_to_roles,
    )


def log_failed_operation(request, event_type, action, description, response_status=None, error_details=None):
    """
    Specialized function for logging failed operations.
    Automatically sets status to 'failed' and severity to appropriate level.
    """
    from .models import ActivityLog
    
    user = getattr(request, 'user', None)
    user_ip = get_client_ip(request)
    username = user.username if user and user.is_authenticated else 'anonymous'
    
    # Determine severity based on response status
    severity = 'low'
    if response_status:
        if 400 <= response_status < 500:
            severity = 'medium'
        elif response_status >= 500:
            severity = 'high'
    
    metadata = {'error_details': error_details} if error_details else {}
    
    return ActivityLog.objects.create(
        user=user,
        username=username,
        user_ip=user_ip,
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        event_type=event_type,
        severity=severity,
        status='failed',
        action=action,
        description=description,
        request_method=request.method,
        request_path=request.path,
        response_status=response_status,
        metadata=metadata,
    )


def cleanup_old_logs(days=90):
    """
    Remove activity logs older than specified days.
    Returns count of deleted logs.
    """
    from datetime import timedelta
    from django.utils import timezone
    
    cutoff_date = timezone.now() - timedelta(days=days)
    
    # Don't delete critical logs
    logs_to_delete = ActivityLog.objects.filter(
        timestamp__lt=cutoff_date,
        severity__in=['info', 'low', 'medium']
    ).exclude(
        event_type__in=['security_event', 'permission_change']
    ).delete()
    
    return logs_to_delete[0]


def get_timeline_data(start_date, end_date, interval='hour'):
    """
    Get timeline data for visualization.
    Returns aggregated counts by time interval.
    """
    from django.db.models.functions import TruncHour, TruncDate
    from django.db.models import Count
    from .models import ActivityLog
    
    queryset = ActivityLog.objects.filter(
        timestamp__gte=start_date,
        timestamp__lte=end_date
    )
    
    if interval == 'hour':
        timeline = queryset.annotate(
            period=TruncHour('timestamp')
        ).values('period').annotate(count=Count('id')).order_by('period')
    else:
        timeline = queryset.annotate(
            period=TruncDate('timestamp')
        ).values('period').annotate(count=Count('id')).order_by('period')
    
    return list(timeline)


def get_event_distribution(start_date=None, end_date=None):
    """
    Get distribution of events by type.
    """
    from .models import ActivityLog
    
    queryset = ActivityLog.objects.all()
    
    if start_date:
        queryset = queryset.filter(timestamp__gte=start_date)
    if end_date:
        queryset = queryset.filter(timestamp__lte=end_date)
    
    distribution = queryset.values('event_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    return list(distribution)


def get_severity_distribution(start_date=None, end_date=None):
    """
    Get distribution of events by severity level.
    """
    from .models import ActivityLog
    
    queryset = ActivityLog.objects.all()
    
    if start_date:
        queryset = queryset.filter(timestamp__gte=start_date)
    if end_date:
        queryset = queryset.filter(timestamp__lte=end_date)
    
    distribution = queryset.values('severity').annotate(
        count=Count('id')
    ).order_by('-count')
    
    return list(distribution)


def get_user_activity_summary(user, days=30):
    """
    Get activity summary for a specific user.
    """
    from datetime import timedelta
    from django.utils import timezone
    from .models import ActivityLog
    
    start_date = timezone.now() - timedelta(days=days)
    
    queryset = ActivityLog.objects.filter(
        user=user,
        timestamp__gte=start_date
    )
    
    summary = {
        'total_actions': queryset.count(),
        'by_event_type': {},
        'by_severity': {},
        'failed_operations': queryset.filter(status='failed').count(),
        'security_events': queryset.filter(
            event_type__in=['login', 'logout', 'permission_change']
        ).count(),
        'last_activity': queryset.order_by('-timestamp').first(),
    }
    
    # Event type breakdown
    for item in queryset.values('event_type').annotate(count=Count('id')):
        summary['by_event_type'][item['event_type']] = item['count']
    
    # Severity breakdown
    for item in queryset.values('severity').annotate(count=Count('id')):
        summary['by_severity'][item['severity']] = item['count']
    
    return summary
