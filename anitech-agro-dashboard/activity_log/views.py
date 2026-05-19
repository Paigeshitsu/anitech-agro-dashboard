"""
Views and API endpoints for Activity Log management.
"""
import csv
import io
import json
import html
import textwrap
from datetime import datetime, timedelta

from django.contrib.auth.decorators import login_required
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Count, Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import ActivityLog, LogAggregation
from .utils import fuzzy_search, get_client_ip, log_activity


EXPORT_FIELD_LABELS = {
    'timestamp': 'Timestamp',
    'username': 'User',
    'event_type': 'Event Type',
    'severity': 'Severity',
    'status': 'Status',
    'action': 'Action',
    'description': 'Description',
    'resource_type': 'Resource Type',
    'resource_name': 'Resource Name',
    'user_ip': 'IP Address',
    'response_status': 'Response Status',
}

DEFAULT_EXPORT_FIELDS = [
    'timestamp',
    'username',
    'event_type',
    'severity',
    'status',
    'action',
    'resource_name',
]


def _parse_request_datetime(value):
    if not value:
        return None

    parsed = parse_datetime(value)
    if parsed is None:
        return None
    if timezone.is_naive(parsed):
        return timezone.make_aware(parsed, timezone.get_current_timezone())
    return parsed


def _normalize_export_fields(raw_fields):
    if isinstance(raw_fields, str):
        candidates = [item.strip() for item in raw_fields.split(',')]
    else:
        candidates = [str(item).strip() for item in raw_fields]

    fields = []
    for field in candidates:
        if field and field in EXPORT_FIELD_LABELS and field not in fields:
            fields.append(field)

    return fields or DEFAULT_EXPORT_FIELDS.copy()


def _format_log_value(log, field):
    value = getattr(log, field, '')

    if field == 'timestamp':
        return timezone.localtime(log.timestamp).strftime('%b %d, %Y %H:%M:%S') if log.timestamp else ''
    if field == 'event_type':
        return log.get_event_type_display()
    if field == 'severity':
        return log.get_severity_display()
    if field == 'status':
        return log.get_status_display()
    if field == 'resource_type':
        return log.get_resource_type_display() if log.resource_type else ''
    if value is None:
        return ''
    if hasattr(value, 'isoformat'):
        return value.isoformat()
    return str(value)


def _build_export_rows(queryset, fields):
    headers = [EXPORT_FIELD_LABELS[field] for field in fields]
    rows = []

    for log in queryset:
        row = {EXPORT_FIELD_LABELS[field]: _format_log_value(log, field) for field in fields}
        rows.append(row)

    return headers, rows


def _has_active_filters(filters):
    return any(value for value in filters.values())


def _scope_logs_for_user(queryset, user):
    if user.account_type in ['admin', 'secretary']:
        return queryset
    if user.account_type in ['farmer', 'buyer']:
        return queryset.filter(
            Q(user=user) |
            Q(user__isnull=True, username=user.username)
        )
    return queryset.filter(
        Q(visible_to_roles__len=0) |
        Q(visible_to_roles__contains=[user.account_type])
    )


class ActivityLogListView(View):
    """
    Main view for displaying activity log with filtering, sorting, and pagination.
    """
    template_name = 'activity_log/list.html'
    
    def get(self, request):
        # Check permissions
        if not request.user.is_authenticated:
            return redirect('login')
        
        if request.user.account_type not in ['admin', 'secretary', 'farmer', 'buyer']:
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
        
        # Get aggregation statistics on a capped sample without slicing the
        # queryset object that _get_statistics() continues to filter.
        stats_sample_ids = list(queryset.values_list('id', flat=True)[:1000])
        stats_queryset = queryset.filter(id__in=stats_sample_ids) if stats_sample_ids else queryset.none()
        stats = self._get_statistics(stats_queryset)
        
        # Pagination
        try:
            page = int(request.GET.get('page', 1))
        except ValueError:
            page = 1
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
            'has_filters': _has_active_filters(filters),
            'stats': stats,
            'page_size': page_size,
            'sort_field': sort_field,
            'sort_direction': sort_direction,
            'total_count': paginator.count,
            'page_numbers': self._get_page_numbers(paginator, logs.number),
            'event_types': ActivityLog.EVENT_TYPES,
            'severity_levels': ActivityLog.SEVERITY_LEVELS,
            'status_choices': ActivityLog.STATUS_CHOICES,
            'resource_types': ActivityLog.RESOURCE_TYPES,
        }
        
        # Check if request is AJAX
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return render(request, 'activity_log/partials/log_table_container.html', context)
        
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
                date_from = _parse_request_datetime(filters['date_from'])
                if date_from:
                    queryset = queryset.filter(timestamp__gte=date_from)
            except:
                pass
        
        if filters['date_to']:
            try:
                date_to = _parse_request_datetime(filters['date_to'])
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
        return _scope_logs_for_user(queryset, user)
    
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
        
        # Check visibility permissions using the same role scoping rules as the list view.
        if not _scope_logs_for_user(ActivityLog.objects.filter(id=log.id), request.user).exists():
            return JsonResponse({'error': 'Access denied'}, status=403)

        # Get related events
        related_events = _scope_logs_for_user(ActivityLog.objects.filter(
            Q(session_id=log.session_id) | Q(related_event=log)
        ).exclude(id=log.id), request.user)[:10]
        
        context = {
            'log': log,
            'related_events': related_events,
        }
        
        wants_partial = (
            request.headers.get('X-Requested-With') == 'XMLHttpRequest'
            or request.GET.get('partial') == '1'
        )

        if wants_partial:
            return render(request, 'activity_log/partials/log_detail.html', context)
        
        return render(request, self.template_name, context)


class ActivityLogExportView(View):
    """
    View for exporting activity logs in various formats.
    """
    
    def get(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Unauthorized'}, status=401)
        
        export_format = request.GET.get('format', 'csv').lower()
        fields = _normalize_export_fields(
            request.GET.get('fields') or request.GET.getlist('fields')
        )

        list_view = ActivityLogListView()
        filters = list_view._get_filters(request)

        queryset = ActivityLog.objects.all()
        queryset = list_view._apply_filters(queryset, filters, request.user).order_by('-timestamp')[:10000]

        if export_format == 'csv':
            return self._export_csv(queryset, fields)
        if export_format == 'excel':
            return self._export_excel(queryset, fields)
        if export_format == 'pdf':
            return self._export_pdf(queryset, fields)
        return JsonResponse({'error': 'Invalid export format'}, status=400)
    
    def _export_csv(self, queryset, fields):
        """Export to CSV format."""
        headers, rows = _build_export_rows(queryset, fields)
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="activity_log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(headers)

        for row in rows:
            writer.writerow([row[header] for header in headers])
        
        return response
    
    def _export_excel(self, queryset, fields):
        """Export to an Excel-compatible XLS file."""
        headers, rows = _build_export_rows(queryset, fields)
        response = HttpResponse(
            content_type='application/vnd.ms-excel; charset=utf-8'
        )
        response['Content-Disposition'] = (
            f'attachment; filename="activity_log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xls"'
        )
        response.write('<html><head><meta charset="utf-8"></head><body>')
        response.write('<table border="1">')
        response.write('<tr>')
        for header in headers:
            response.write(f'<th>{html.escape(header)}</th>')
        response.write('</tr>')

        for row in rows:
            response.write('<tr>')
            for header in headers:
                response.write(f'<td>{html.escape(str(row[header]))}</td>')
            response.write('</tr>')

        response.write('</table></body></html>')
        return response
    
    def _export_pdf(self, queryset, fields):
        """Export to PDF format."""
        headers, rows = _build_export_rows(queryset, fields)
        export_timestamp = timezone.localtime().strftime('%b %d, %Y %H:%M:%S')
        lines = [
            'Activity Log Report',
            f'Exported: {export_timestamp}',
            '',
            ' | '.join(headers),
            '-' * min(len(' | '.join(headers)), 110),
        ]

        if rows:
            for row in rows:
                raw_line = ' | '.join(str(row[header]) for header in headers)
                lines.extend(textwrap.wrap(raw_line, width=110) or [''])
                lines.append('')
        else:
            lines.append('No activity logs found for the selected filters.')

        pdf_bytes = self._render_simple_pdf(lines)
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="activity_log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
        return response

    def _render_simple_pdf(self, lines):
        """Generate a simple text-based PDF without external dependencies."""
        lines_per_page = 45
        pages = [lines[i:i + lines_per_page] for i in range(0, len(lines), lines_per_page)] or [[]]

        objects = []

        def add_object(content):
            objects.append(content)
            return len(objects)

        font_id = add_object("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
        page_ids = []
        content_ids = []

        def pdf_escape(value):
            return value.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')

        for page_lines in pages:
            text_commands = ["BT", "/F1 10 Tf", "50 780 Td", "14 TL"]
            for line in page_lines:
                text_commands.append(f"({pdf_escape(line)}) Tj")
                text_commands.append("T*")
            text_commands.append("ET")
            stream = '\n'.join(text_commands).encode('latin-1', errors='replace')
            content_id = add_object(
                f"<< /Length {len(stream)} >>\nstream\n{stream.decode('latin-1')}\nendstream"
            )
            content_ids.append(content_id)
            page_ids.append(add_object(
                f"<< /Type /Page /Parent PAGES_ID 0 R /MediaBox [0 0 612 792] /Contents {content_id} 0 R /Resources << /Font << /F1 {font_id} 0 R >> >> >>"
            ))

        kids = ' '.join(f'{page_id} 0 R' for page_id in page_ids)
        pages_id = add_object(f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>")
        catalog_id = add_object(f"<< /Type /Catalog /Pages {pages_id} 0 R >>")

        rendered_objects = []
        for index, obj in enumerate(objects, start=1):
            rendered_objects.append(f"{index} 0 obj\n{obj.replace('PAGES_ID', str(pages_id))}\nendobj\n")

        pdf = "%PDF-1.4\n"
        offsets = []
        for obj in rendered_objects:
            offsets.append(len(pdf.encode('latin-1')))
            pdf += obj

        xref_offset = len(pdf.encode('latin-1'))
        pdf += f"xref\n0 {len(rendered_objects) + 1}\n"
        pdf += "0000000000 65535 f \n"
        for offset in offsets:
            pdf += f"{offset:010d} 00000 n \n"
        pdf += (
            f"trailer\n<< /Size {len(rendered_objects) + 1} /Root {catalog_id} 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF"
        )
        return pdf.encode('latin-1', errors='replace')


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
        
        queryset = _scope_logs_for_user(queryset, request.user)
        
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
        
        queryset = _scope_logs_for_user(ActivityLog.objects.all(), request.user)
        
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
    
    count = _scope_logs_for_user(ActivityLog.objects.filter(
        timestamp__gte=since
    ), request.user).count()
    
    return JsonResponse({'count': count})


@login_required
def jump_to_date(request, year, month, day):
    """
    Navigate to a specific date in the activity log.
    """
    try:
        target_date = datetime(int(year), int(month), int(day))
        next_day = target_date + timedelta(days=1)
        
        queryset = _scope_logs_for_user(ActivityLog.objects.filter(
            timestamp__gte=target_date,
            timestamp__lt=next_day
        ), request.user)
        
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
