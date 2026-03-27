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
        
        # Login/logout events
        if '/auth/login' in request.path:
            return 'login' if response.status_code < 400 else None
        if '/auth/logout' in request.path:
            return 'logout'
        
        # CRUD operations
        if method in ['POST']:
            if '/create' in request.path or '/add' in request.path:
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
                # Try to get username from request body
                try:
                    body = json.loads(request.body) if hasattr(request, 'body') else {}
                    username = body.get('username', 'Unknown')
                    action = f"User '{username}' logged in"
                except:
                    pass
            
            # For logout events, the user is still authenticated at this point
            if event_type == 'logout' and user_for_log.is_authenticated:
                action = f"User '{user_for_log.username}' logged out"
            
            # Get request payload (for POST/PUT/PATCH)
            request_payload = None
            if request.method in ['POST', 'PUT', 'PATCH'] and hasattr(request, 'body'):
                try:
                    request_payload = json.loads(request.body)
                    # Remove sensitive fields
                    if 'password' in request_payload:
                        request_payload['password'] = '[REDACTED]'
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
