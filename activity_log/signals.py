"""
Signal handlers for automatic activity logging.
"""
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.utils import timezone

from .models import ActivityLog


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """
    Signal handler for user login events.
    Automatically logs when a user successfully logs in.
    """
    try:
        from .utils import get_client_ip
        
        user_ip = get_client_ip(request) if request else None
        user_agent = request.META.get('HTTP_USER_AGENT', '') if request else ''
        
        ActivityLog.objects.create(
            user=user,
            username=user.username,
            user_ip=user_ip,
            user_agent=user_agent,
            event_type='login',
            severity='medium',
            status='success',
            action=f"User '{user.username}' logged in",
            description=f"User {user.username} ({user.email}) successfully logged in from IP {user_ip or 'Unknown'}",
            request_path=request.path if request else '/',
            request_method='POST' if request else 'GET',
            session_id=request.session.session_key if request else None,
        )
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error logging user login: {str(e)}")


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """
    Signal handler for user logout events.
    Automatically logs when a user logs out.
    """
    try:
        from .utils import get_client_ip
        
        if user is None:
            return
            
        user_ip = get_client_ip(request) if request else None
        user_agent = request.META.get('HTTP_USER_AGENT', '') if request else ''
        
        ActivityLog.objects.create(
            user=user,
            username=user.username,
            user_ip=user_ip,
            user_agent=user_agent,
            event_type='logout',
            severity='medium',
            status='success',
            action=f"User '{user.username}' logged out",
            description=f"User {user.username} ({user.email}) logged out",
            request_path=request.path if request else '/',
            request_method='POST' if request else 'GET',
            session_id=request.session.session_key if request else None,
        )
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error logging user logout: {str(e)}")


def connect_activity_log_signals():
    """
    Connect all activity log signals.
    Call this function in AppConfig.ready() to enable automatic logging.
    """
    # Signals are already connected via @receiver decorator
    pass


def disconnect_activity_log_signals():
    """
    Disconnect all activity log signals.
    Useful for testing or when you want to disable automatic logging.
    """
    user_logged_in.disconnect(log_user_login)
    user_logged_out.disconnect(log_user_logout)
