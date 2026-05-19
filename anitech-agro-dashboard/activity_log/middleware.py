"""
Middleware for automatic activity logging.
"""
import json
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings


class ActivityLogMiddleware(MiddlewareMixin):
    """
    Middleware that automatically logs user activities.
    """
    
    # Paths to exclude from logging
    EXCLUDED_PATHS = [
        '/static/',
        '/media/',
        '/favicon.ico',
        '/health/',
        '/metrics/',
    ]
    
    # Paths that should be logged as read operations
    READ_METHODS = ['GET', 'HEAD', 'OPTIONS']
    
    def process_request(self, request):
        # Store the start time for response time calculation
        request._activity_start_time = None
        try:
            request._activity_start_time = getattr(request, 'request_start_time', None) or self._get_timestamp()
        except:
            pass
    
    def process_response(self, request, response):
        # Skip if path is excluded
        if self._should_skip(request.path):
            return response
        
        # Only log for authenticated users
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return response
        
        # Determine event type based on request method
        event_type = self._get_event_type(request, response)
        
        # Only log significant events
        if event_type:
            self._log_activity(request, response, event_type)
        
        return response
    
    def _should_skip(self, path):
        """Check if the path should be skipped from logging."""
        for excluded in self.EXCLUDED_PATHS:
            if path.startswith(excluded):
                return True
        return False
    
    def _get_event_type(self, request, response):
        """Determine the event type based on request method and response status."""
        method = request.method
        path = request.path
        lowered_path = path.lower()

        explicit_log_paths = [
            '/weather/',
            '/crops/add/',
            '/crops/',
            '/market/prices/',
            '/market/offers/',
            '/market/schedules/',
            '/market/sell-offers/',
        ]
        if any(path.startswith(item) for item in explicit_log_paths):
            return None
        
        # Login/logout events
        if '/auth/login' in path:
            return None
        if '/auth/logout' in path:
            return None
        
        # CRUD operations
        if method in ['POST']:
            if any(token in lowered_path for token in ['/delete/', '/remove/']):
                return 'delete'
            if any(token in lowered_path for token in ['/edit/', '/update/', '/status/']):
                return 'update'
            if '/create' in lowered_path or '/add' in lowered_path:
                return 'create'
            return 'create'
        elif method in ['PUT', 'PATCH']:
            return 'update'
        elif method in ['DELETE']:
            return 'delete'
        elif method in self.READ_METHODS:
            # Only log significant reads, not static files or list views
            if response.status_code == 200 and '/static/' not in request.path:
                return 'read'
        
        return None
    
    def _get_timestamp(self):
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now()
    
    def _log_activity(self, request, response, event_type):
        """Log the activity asynchronously."""
        try:
            from activity_log.utils import log_activity
            from activity_log.models import ActivityLog
            
            # Determine severity based on response status
            severity = 'info'
            status = 'success'
            
            if response.status_code >= 500:
                severity = 'critical'
                status = 'failed'
            elif response.status_code >= 400:
                severity = 'medium'
                status = 'failed'
            elif response.status_code >= 300:
                severity = 'low'
            
            # Extract resource information from path
            resource_type, resource_id = self._extract_resource(request.path)
            
            # Get action description
            action = self._get_action_description(request, event_type, resource_type)
            
            # For login events, capture the user attempting to log in
            user_for_log = request.user
            if event_type == 'login' and not user_for_log.is_authenticated:
                # Form logins may already have consumed the request stream, so
                # prefer POST data and fall back to JSON only when available.
                try:
                    username = request.POST.get('username')
                    content_type = request.META.get('CONTENT_TYPE', '')
                    if not username and 'application/json' in content_type:
                        body = json.loads(request.body)
                        username = body.get('username')
                    if username:
                        action = f"User '{username}' logged in"
                except:
                    pass
            
            # For logout events, the user is still authenticated at this point
            if event_type == 'logout' and user_for_log.is_authenticated:
                action = f"User '{user_for_log.username}' logged out"
            
            # Get request payload (for POST/PUT/PATCH)
            request_payload = None
            if request.method in ['POST', 'PUT', 'PATCH']:
                # Skip reading body for multipart/form-data (file uploads) as it can only be read once
                content_type = request.META.get('CONTENT_TYPE', '')
                try:
                    if 'application/json' in content_type:
                        request_payload = json.loads(request.body)
                    else:
                        request_payload = request.POST.dict()

                    if request_payload:
                        # Remove sensitive fields
                        if 'password' in request_payload:
                            request_payload['password'] = '[REDACTED]'
                        if 'password1' in request_payload:
                            request_payload['password1'] = '[REDACTED]'
                        if 'password2' in request_payload:
                            request_payload['password2'] = '[REDACTED]'
                        if 'token' in request_payload:
                            request_payload['token'] = '[REDACTED]'
                except:
                    pass
            
            # Log the activity
            log_entry = log_activity(
                request=request,
                event_type=event_type,
                severity=severity,
                status=status,
                action=action,
                description=f"{request.method} {request.path} by {user_for_log.username if user_for_log.is_authenticated else 'Anonymous'}",
                resource_type=resource_type,
                resource_id=resource_id or '',
                request_payload=request_payload,
                response_status=response.status_code,
            )
            
            # For login events, update with the authenticated user
            if event_type == 'login' and user_for_log.is_authenticated and log_entry:
                log_entry.user = user_for_log
                log_entry.username = user_for_log.username
                log_entry.save()
                
        except Exception as e:
            # Don't let logging errors affect the main request
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error logging activity: {str(e)}")
    
    def _extract_resource(self, path):
        """Extract resource type and ID from the request path."""
        parts = [p for p in path.strip('/').split('/') if p]
        
        resource_type = ''
        resource_id = ''
        
        for i, part in enumerate(parts):
            # Check if this looks like an ID
            if part.isdigit():
                resource_id = part
                if i > 0:
                    resource_type = parts[i-1]
                break
            elif i > 0 and parts[i-1] in ['edit', 'update', 'delete', 'detail']:
                resource_type = part
                break
        
        # Map common path segments to resource types
        resource_map = {
            'crops': 'crop',
            'market': 'market',
            'notifications': 'notification',
            'schedule': 'schedule',
            'inventory': 'inventory',
            'users': 'user',
            'profile': 'user',
        }
        
        if resource_type in resource_map:
            resource_type = resource_map[resource_type]
        
        return resource_type, resource_id
    
    def _get_action_description(self, request, event_type, resource_type):
        """Generate a human-readable action description."""
        path = request.path.lower()
        payload = getattr(request, 'POST', None) or {}

        crop_name = payload.get('crop_name') or payload.get('crop')
        offer_crop_name = payload.get('crop_name') or payload.get('crop')
        schedule_title = payload.get('title')

        if '/weather/' in path and event_type == 'read':
            return 'Viewed weather forecast'
        if '/dashboard/' in path and event_type == 'read':
            return 'Viewed dashboard'
        if '/activity-log/' in path and event_type == 'read':
            return 'Viewed activity log'
        if '/notifications/' in path and event_type == 'read':
            return 'Viewed notifications'
        if '/profile/' in path and event_type == 'read':
            return 'Viewed profile'
        if '/market/prices/' in path and event_type == 'read':
            return 'Viewed market prices'
        if '/market/offers/' in path and event_type == 'read':
            return 'Viewed buyer offers'
        if '/market/sell-offers/' in path and event_type == 'read':
            return 'Viewed sell offers'
        if '/market/schedules/' in path and event_type == 'read':
            return 'Viewed distribution schedules'
        if '/crops/' in path and event_type == 'read':
            return 'Viewed crops'
        if '/crops/add/' in path and event_type == 'create':
            return f'Added crop: {crop_name}' if crop_name else 'Added crop'
        if '/crops/' in path and '/edit/' in path and event_type == 'update':
            return f'Updated crop: {crop_name}' if crop_name else 'Updated crop'
        if '/crops/' in path and '/delete/' in path and event_type == 'delete':
            return 'Deleted crop'
        if '/purchase/' in path and event_type == 'create':
            return 'Purchased crop'
        if '/offers/add/' in path and event_type == 'create':
            return f'Made offer on {offer_crop_name}' if offer_crop_name else 'Made buyer offer'
        if '/offers/' in path and '/status/' in path and event_type == 'update':
            return f'Updated buyer offer status to {payload.get("status")}'
        if '/sell-offers/add/' in path and event_type == 'create':
            return f'Posted sell offer for {offer_crop_name}' if offer_crop_name else 'Posted sell offer'
        if '/prices/add/' in path and event_type == 'create':
            crop = payload.get('crop_name')
            price = payload.get('current_price')
            return f'Added market price: {crop} is now {price}' if crop and price else 'Added market price'
        if '/prices/' in path and '/edit/' in path and event_type == 'update':
            crop = payload.get('crop_name')
            price = payload.get('current_price')
            return f'Updated market price: {crop} is now {price}' if crop and price else 'Updated market price'
        if '/prices/' in path and '/delete/' in path and event_type == 'delete':
            return 'Deleted market price entry'
        if '/schedules/add/' in path and event_type == 'create':
            return f'Added distribution schedule: {schedule_title}' if schedule_title else 'Added distribution schedule'
        if '/schedules/' in path and '/edit/' in path and event_type == 'update':
            return f'Updated distribution schedule: {schedule_title}' if schedule_title else 'Updated distribution schedule'
        if '/schedules/' in path and '/delete/' in path and event_type == 'delete':
            return 'Deleted distribution schedule'

        resource_name = resource_type.replace('_', ' ').title() if resource_type else 'Resource'
        
        descriptions = {
            'login': f"User logged in",
            'logout': f"User logged out",
            'create': f"Created new {resource_name}",
            'read': f"Viewed {resource_name}",
            'update': f"Updated {resource_name}",
            'delete': f"Deleted {resource_name}",
        }
        
        return descriptions.get(event_type, f"{event_type.title()} {resource_name}")
