from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .models import Notification, ActivityLog
import json
from datetime import datetime, timedelta


@login_required
def activity_log_view(request):
    """Display activity log for the current user (or all if admin)"""
    if request.user.account_type == 'admin':
        # Admin sees all activity logs
        activities = ActivityLog.objects.all().order_by('-created_at')[:50]
    else:
        # Regular users see only their own activities
        activities = ActivityLog.objects.filter(user=request.user).order_by('-created_at')[:50]
    
    context = {
        'activities': activities,
        'page_title': 'Activity Log'
    }
    return render(request, 'activity_log.html', context)


@login_required
@require_http_methods(["GET"])
def notifications_api(request):
    """API endpoint to fetch notifications for the current user"""
    action = request.GET.get('action', 'fetch')
    
    if action == 'fetch':
        # Get user's notifications
        notifications = Notification.objects.filter(
            user=request.user
        ).order_by('-created_at')[:20]
        
        unread_count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()
        
        notifications_data = []
        for notif in notifications:
            notifications_data.append({
                'id': notif.id,
                'type': notif.type,
                'title': notif.title,
                'message': notif.message,
                'is_read': notif.is_read,
                'created_at': notif.created_at.isoformat(),
                'time_ago': get_time_ago(notif.created_at)
            })
        
        return JsonResponse({
            'success': True,
            'notifications': notifications_data,
            'unread_count': unread_count
        })
    
    return JsonResponse({'success': False, 'message': 'Invalid action'})


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def mark_notification_read(request):
    """API endpoint to mark a notification as read"""
    try:
        data = json.loads(request.body)
        notification_id = data.get('id')
        
        if notification_id == 0:
            # Mark all as read
            Notification.objects.filter(
                user=request.user,
                is_read=False
            ).update(is_read=True)
            return JsonResponse({'success': True, 'message': 'All notifications marked as read'})
        
        if notification_id:
            notification = Notification.objects.filter(
                id=notification_id,
                user=request.user
            ).first()
            
            if notification:
                notification.is_read = True
                notification.save()
                return JsonResponse({'success': True})
        
        return JsonResponse({'success': False, 'message': 'Notification not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
@require_http_methods(["GET"])
def get_unread_count(request):
    """API endpoint to get unread notification count"""
    count = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).count()
    
    return JsonResponse({'unread_count': count})


def get_time_ago(dt):
    """Calculate time ago string from datetime"""
    from django.utils import timezone
    now = timezone.now()
    # Make dt timezone-aware if it's naive
    if dt.tzinfo is None:
        from django.utils.timezone import make_aware
        dt = make_aware(dt)
    diff = now - dt
    
    if diff.days > 365:
        return f"{diff.days // 365} year(s) ago"
    elif diff.days > 30:
        return f"{diff.days // 30} month(s) ago"
    elif diff.days > 0:
        return f"{diff.days} day(s) ago"
    elif diff.seconds > 3600:
        return f"{diff.seconds // 3600} hour(s) ago"
    elif diff.seconds > 60:
        return f"{diff.seconds // 60} minute(s) ago"
    else:
        return "Just now"


def create_notification(user, notif_type, title, message):
    """Helper function to create a notification"""
    Notification.objects.create(
        user=user,
        type=notif_type,
        title=title,
        message=message
    )
