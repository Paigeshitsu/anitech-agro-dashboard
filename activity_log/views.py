"""
Views and API endpoints for Activity Log management.
"""
import json
import csv
import io
from datetime import datetime, timedelta
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views import View
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Count, F
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from .models import ActivityLog, LogAggregation
from .utils import fuzzy_search, get_client_ip, log_activity


class ActivityLogListView(View):
    """
    Main view for displaying activity log with filtering, sorting, and pagination.
    """
    template_name = 'activity_log/list.html'
    
    def get(self, request):
        # Check permissions
        if not request.user.is_authenticated:
            return redirect('login')
        
        if request.user.account_type not in ['admin', 'secretary']:
            return render(request, 'error.html', {
                'message': 'You do not have permission to view activity logs.'
            })
        
        # Get filter parameters
        filters = self._get_filters(request)
        
        # Get queryset with filters
        queryset = ActivityLog.objects.all()
        queryset = self._apply_filters(queryset, filters, request.user)
        
        # Apply sorting
        sort_field = request.GET.get('sort', 'timestamp')
        sort_direction = request.GET.get('direction', 'desc')
        queryset = self._apply_sorting(queryset, sort_field, sort_direction)
        
        # Get aggregation statistics
        stats = self._get_statistics(queryset[:1000])
        
        # Pagination
        page = request.GET.get('page', 1)
        page_size = int(request.GET.get('page_size', 25))
        paginator = Paginator(queryset, page_size)
        
        try:
            logs = paginator.page(page)
        except PageNotAnInteger:
            logs = paginator.page(1)
        except EmptyPage:
            logs = paginator.page(paginator.num_pages)
        
        context = {
            'logs': logs,
            'filters': filters,
            'stats': stats,
            'page_size': page_size,
            'sort_field': sort_field,
            'sort_direction': sort_direction,
            'total_count': paginator.count,
            'page_numbers': self._get_page_numbers(paginator, page),
            'event_types': ActivityLog.EVENT_TYPES,
            'severity_levels': ActivityLog.SEVERITY_LEVELS,
            'status_choices': ActivityLog.STATUS_CHOICES,
            'resource_types': ActivityLog.RESOURCE_TYPES,
        }
        
        # Check if request is AJAX
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return render(request, 'activity_log/partials/log_table.html', context)
        
        return render(request, self.template_name, context)
    
    def _get_filters(self, request):
        """Extract filter parameters from request."""
        return {
            'date_from': request.GET.get('date_from', ''),
            'date_to': request.GET.get('date_to', ''),
            'user': request.GET.get('user', ''),
            'event_type': request.GET.get('event_type', ''),
            'severity': request.GET.get('severity', ''),
            'status': request.GET.get('status', ''),
            'resource_type': request.GET.get('resource_type', ''),
            'search': request.GET.get('search', ''),
            'ip_address': request.GET.get('ip_address', ''),
        }
    
    def _apply_filters(self, queryset, filters, user):
        """Apply filters to queryset."""
        # Date range filter
        if filters['date_from']:
            try:
                date_from = parse_datetime(filters['date_from'])
                if date_from:
                    queryset = queryset.filter(timestamp__gte=date_from)
            except:
                pass
        
        if filters['date_to']:
            try:
                date_to = parse_datetime(filters['date_to'])
                if date_to:
                    queryset = queryset.filter(timestamp__lte=date_to)
            except:
                pass
        
        # User filter
        if filters['user']:
            queryset = queryset.filter(
                Q(username__icontains=filters['user']) |
                Q(user__email__icontains=filters['user'])
            )
        
        # Event type filter
        if filters['event_type']:
            queryset = queryset.filter(event_type=filters['event_type'])
        
        # Severity filter
        if filters['severity']:
            queryset = queryset.filter(severity=filters['severity'])
        
        # Status filter
        if filters['status']:
            queryset = queryset.filter(status=filters['status'])
        
        # Resource type filter
        if filters['resource_type']:
            queryset = queryset.filter(resource_type=filters['resource_type'])
        
        # IP address filter
        if filters['ip_address']:
            queryset = queryset.filter(user_ip__icontains=filters['ip_address'])
        
        # Fuzzy search across all fields
        if filters['search']:
            search_term = filters['search']
            queryset = fuzzy_search(queryset, search_term)
        
        # Role-based visibility filter
        if user.account_type != 'admin':
            queryset = queryset.filter(
                Q(visible_to_roles__len=0) |
                Q(visible_to_roles__contains=[user.account_type])
            )
        
        return queryset
    
    def _apply_sorting(self, queryset, sort_field, direction):
        """Apply sorting to queryset."""
        if direction == 'desc':
            sort_field = f'-{sort_field}'
        allowed_fields = ['timestamp', 'username', 'event_type', 'resource_name', 
                         'user_ip', 'status', 'severity', 'action']
        if sort_field.lstrip('-') in allowed_fields:
            return queryset.order_by(sort_field)
        return queryset.order_by('-timestamp')
    
    def _get_statistics(self, queryset):
        """Calculate aggregation statistics."""
        stats = {
            'total': queryset.count(),
            'by_event_type': {},
            'by_severity': {},
            'by_status': {},
            'critical_count': 0,
            'failed_count': 0,
            'security_events': 0,
        }
        
        # Event type distribution
        event_counts = queryset.values('event_type').annotate(count=Count('id'))
        for item in event_counts:
            stats['by_event_type'][item['event_type']] = item['count']
        
        # Severity distribution
        severity_counts = queryset.values('severity').annotate(count=Count('id'))
        for item in severity_counts:
            stats['by_severity'][item['severity']] = item['count']
        
        # Status distribution
        status_counts = queryset.values('status').annotate(count=Count('id'))
        for item in status_counts:
            stats['by_status'][item['status']] = item['count']
        
        # Critical and failed counts
        stats['critical_count'] = queryset.filter(severity='critical').count()
        stats['failed_count'] = queryset.filter(status='failed').count()
        stats['security_events'] = queryset.filter(
            event_type__in=['login', 'logout', 'security_event', 'permission_change']
        ).count()
        
        return stats
    
    def _get_page_numbers(self, paginator, current_page):
        """Generate page numbers for pagination display."""
        try:
            current_page = int(current_page)
        except:
            current_page = 1
        
        total_pages = paginator.num_pages
        page_range = 5
        
        start = max(1, current_page - page_range)
        end = min(total_pages, current_page + page_range)
        
        return list(range(start, end + 1))


class ActivityLogDetailView(View):
    """
    View for displaying detailed information about a single activity log entry.
    """
    template_name = 'activity_log/detail.html'
    
    def get(self, request, log_id):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Unauthorized'}, status=401)
        
        try:
            log = ActivityLog.objects.get(id=log_id)
        except ActivityLog.DoesNotExist:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': 'Log not found'}, status=404)
            return render(request, 'error.html', {'message': 'Log entry not found.'})
        
        # Check visibility permissions
        if log.visible_to_roles and request.user.account_type not in log.visible_to_roles:
            if request.user.account_type != 'admin':
                return JsonResponse({'error': 'Access denied'}, status=403)
        
        # Get related events
        related_events = ActivityLog.objects.filter(
            Q(session_id=log.session_id) | Q(related_event=log)
        ).exclude(id=log.id)[:10]
        
        context = {
            'log': log,
            'related_events': related_events,
        }
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return render(request, 'activity_log/partials/log_detail.html', context)
        
        return render(request, self.template_name, context)


class ActivityLogExportView(View):
    """
    View for exporting activity logs in various formats.
    """
    
    def get(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Unauthorized'}, status=401)
        
        export_format = request.GET.get('format', 'csv')
        fields = request.GET.getlist('fields', [])
        
        # Get filters from request
        filters = {
            'date_from': request.GET.get('date_from', ''),
            'date_to': request.GET.get('date_to', ''),
            'user': request.GET.get('user', ''),
            'event_type': request.GET.get('event_type', ''),
            'severity': request.GET.get('severity', ''),
            'status': request.GET.get('status', ''),
            'resource_type': request.GET.get('resource_type', ''),
            'search': request.GET.get('search', ''),
        }
        
        # Apply filters
        queryset = ActivityLog.objects.all()
        if request.user.account_type != 'admin':
            queryset = queryset.filter(
                Q(visible_to_roles__len=0) |
                Q(visible_to_roles__contains=[request.user.account_type])
            )
        
        # Apply date filters
        if filters['date_from']:
            date_from = parse_datetime(filters['date_from'])
            if date_from:
                queryset = queryset.filter(timestamp__gte=date_from)
        
        if filters['date_to']:
            date_to = parse_datetime(filters['date_to'])
            if date_to:
                queryset = queryset.filter(timestamp__lte=date_to)
        
        # Limit export size
        queryset = queryset[:10000]
        
        # Export based on format
        if export_format == 'csv':
            return self._export_csv(queryset, fields)
        elif export_format == 'json':
            return self._export_json(queryset, fields)
        elif export_format == 'pdf':
            return self._export_pdf(queryset, fields)
        else:
            return JsonResponse({'error': 'Invalid export format'}, status=400)
    
    def _export_csv(self, queryset, fields):
        """Export to CSV format."""
        if not fields:
            fields = ['timestamp', 'username', 'event_type', 'severity', 'status',
                     'resource_type', 'action', 'user_ip', 'response_status']
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="activity_log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(fields)
        
        for log in queryset:
            row = []
            for field in fields:
                value = getattr(log, field, '')
                if hasattr(value, 'isoformat'):
                    value = value.isoformat()
                row.append(str(value) if value else '')
            writer.writerow(row)
        
        return response
    
    def _export_json(self, queryset, fields):
        """Export to JSON format."""
        if not fields:
            fields = ['id', 'timestamp', 'username', 'event_type', 'severity',
                     'status', 'resource_type', 'resource_name', 'action',
                     'description', 'user_ip', 'request_method', 'request_path']
        
        data = []
        for log in queryset:
            item = {}
            for field in fields:
                value = getattr(log, field, '')
                if hasattr(value, 'isoformat'):
                    value = value.isoformat()
                item[field] = str(value) if value else ''
            data.append(item)
        
        response = HttpResponse(json.dumps(data, indent=2), content_type='application/json')
        response['Content-Disposition'] = f'attachment; filename="activity_log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json"'
        return response
    
    def _export_pdf(self, queryset, fields):
        """Export to PDF format."""
        # For PDF, we'll use HTML-to-PDF approach
        html = render(None, 'activity_log/export_pdf.html', {
            'logs': queryset,
            'fields': fields,
            'export_date': datetime.now(),
        }).content.decode('utf-8')
        
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="activity_log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
        
        # Simple HTML to PDF (in production, use WeasyPrint or similar)
        response.write(html.encode('utf-8'))
        return response


class ActivityLogStatsView(View):
    """
    API view for getting aggregation statistics.
    """
    
    def get(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Unauthorized'}, status=401)
        
        period = request.GET.get('period', 'day')
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')
        
        # Default to last 7 days
        if not date_from:
            date_from = (timezone.now() - timedelta(days=7)).isoformat()
        if not date_to:
            date_to = timezone.now().isoformat()
        
        queryset = ActivityLog.objects.filter(
            timestamp__gte=parse_datetime(date_from),
            timestamp__lte=parse_datetime(date_to)
        )
        
        if request.user.account_type != 'admin':
            queryset = queryset.filter(
                Q(visible_to_roles__len=0) |
                Q(visible_to_roles__contains=[request.user.account_type])
            )
        
        # Get hourly/daily distribution
        if period == 'hour':
            stats = queryset.extra(
                select={'period': "strftime('%%Y-%%m-%%d %%H:00', timestamp)"}
            ).values('period').annotate(count=Count('id')).order_by('period')
        else:
            stats = queryset.extra(
                select={'period': "strftime('%%Y-%%m-%%d', timestamp)"}
            ).values('period').annotate(count=Count('id')).order_by('period')
        
        # Event type distribution
        event_dist = queryset.values('event_type').annotate(count=Count('id'))
        
        # Severity distribution
        severity_dist = queryset.values('severity').annotate(count=Count('id'))
        
        # Top users
        top_users = queryset.values('username').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        # Top IP addresses
        top_ips = queryset.filter(
            user_ip__isnull=False
        ).values('user_ip').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        return JsonResponse({
            'timeline': list(stats),
            'event_distribution': list(event_dist),
            'severity_distribution': list(severity_dist),
            'top_users': list(top_users),
            'top_ips': list(top_ips),
            'total_count': queryset.count(),
        })


@require_http_methods(["GET", "POST"])
@csrf_exempt
def activity_log_api(request):
    """
    REST API endpoint for activity log CRUD operations.
    """
    if request.method == 'GET':
        # List logs with pagination
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 25))
        
        queryset = ActivityLog.objects.all()
        
        # Apply filters
        if request.GET.get('user'):
            queryset = queryset.filter(username__icontains=request.GET['user'])
        if request.GET.get('event_type'):
            queryset = queryset.filter(event_type=request.GET['event_type'])
        if request.GET.get('severity'):
            queryset = queryset.filter(severity=request.GET['severity'])
        if request.GET.get('status'):
            queryset = queryset.filter(status=request.GET['status'])
        
        # Pagination
        paginator = Paginator(queryset, page_size)
        try:
            logs = paginator.page(page)
        except PageNotAnInteger:
            logs = paginator.page(1)
        except EmptyPage:
            logs = paginator.page(paginator.num_pages)
        
        return JsonResponse({
            'logs': [{
                'id': log.id,
                'timestamp': log.timestamp.isoformat(),
                'username': log.username,
                'event_type': log.event_type,
                'severity': log.severity,
                'status': log.status,
                'action': log.action,
                'resource_type': log.resource_type,
                'resource_name': log.resource_name,
                'user_ip': log.user_ip,
            } for log in logs],
            'page': page,
            'total_pages': paginator.num_pages,
            'total_count': paginator.count,
            'has_next': logs.has_next(),
            'has_previous': logs.has_previous(),
        })
    
    elif request.method == 'POST':
        # Create new log entry (for manual logging)
        try:
            data = json.loads(request.body)
            log = ActivityLog.objects.create(
                user=request.user if request.user.is_authenticated else None,
                username=request.user.username if request.user.is_authenticated else data.get('username', 'system'),
                event_type=data.get('event_type', 'system'),
                severity=data.get('severity', 'info'),
                status=data.get('status', 'success'),
                action=data.get('action', ''),
                description=data.get('description', ''),
                resource_type=data.get('resource_type', ''),
                resource_id=data.get('resource_id', ''),
                resource_name=data.get('resource_name', ''),
                user_ip=get_client_ip(request),
                request_method=request.method,
                request_path=request.path,
            )
            return JsonResponse({
                'success': True,
                'log_id': log.id,
            })
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)


@require_http_methods(["GET"])
@csrf_exempt
def activity_log_badge(request):
    """
    API endpoint to get count of new entries since last check.
    Used for real-time notification badge.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'count': 0})
    
    last_check = request.GET.get('since')
    if last_check:
        try:
            since = parse_datetime(last_check)
        except:
            since = timezone.now() - timedelta(minutes=5)
    else:
        since = timezone.now() - timedelta(minutes=5)
    
    count = ActivityLog.objects.filter(
        timestamp__gte=since
    ).count()
    
    return JsonResponse({'count': count})


@login_required
def jump_to_date(request, year, month, day):
    """
    Navigate to a specific date in the activity log.
    """
    try:
        target_date = datetime(int(year), int(month), int(day))
        next_day = target_date + timedelta(days=1)
        
        queryset = ActivityLog.objects.filter(
            timestamp__gte=target_date,
            timestamp__lt=next_day
        )
        
        # Find the first page containing these logs
        paginator = Paginator(queryset, 25)
        
        return JsonResponse({
            'success': True,
            'date': target_date.isoformat(),
            'count': paginator.count,
            'page': 1,
        })
    except ValueError:
        return JsonResponse({'error': 'Invalid date'}, status=400)
