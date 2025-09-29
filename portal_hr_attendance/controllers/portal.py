# -*- coding: utf-8 -*-

import base64
import csv
import logging
from io import StringIO
from datetime import datetime, timedelta

from odoo import http, fields, _
from odoo.exceptions import UserError, ValidationError
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager

_logger = logging.getLogger(__name__)


class PortalAttendance(CustomerPortal):
    
    _items_per_page = 20

    # @http.route(['/my/attendance/test'], type='http', auth="public")
    # def test_attendance_route(self, **kw):
    #     """Test route to verify controller is working"""
    #     return "<h1>Portal Attendance Module Test</h1><p>Controller is working correctly!</p>"

    def _prepare_portal_layout_values(self):
        """Add attendance to portal counters"""
        values = super()._prepare_portal_layout_values()
        values['page_name'] = 'attendance'
        return values

    def _prepare_home_portal_values(self, counters):
        """Add attendance info to portal home"""
        values = super()._prepare_home_portal_values(counters)
        
        if 'attendance_count' in counters:
            try:
                employee = request.env['hr.employee'].get_portal_employee()
                attendance_count = request.env['hr.attendance'].search_count([
                    ('employee_id', '=', employee.id)
                ])
                values['attendance_count'] = attendance_count
            except (UserError, ValidationError):
                values['attendance_count'] = 0
                
        return values

    @http.route(['/my'], type='http', auth="user", website=True)
    def home(self, **kw):
        """Override home to include attendance counter"""
        values = self._prepare_home_portal_values(['attendance_count'])
        return request.render("portal.portal_my_home", values)


    @http.route(['/my/attendance', '/my/attendance/page/<int:page>'], type='http', auth="user")
    def portal_attendance_dashboard(self, page=1, sortby=None, filterby=None, search=None, **kw):
        """Main attendance dashboard"""
        try:
            employee = request.env['hr.employee'].get_portal_employee()
        except (UserError, ValidationError) as e:
            return request.render('portal_hr_attendance.portal_no_access', {'error_message': str(e)})

        # Get current status
        status_info = employee.get_current_attendance_status()
        
        # Get today's attendance
        today = fields.Date.today()
        today_attendances = request.env['hr.attendance'].search([
            ('employee_id', '=', employee.id),
            ('check_in', '>=', today),
            ('check_in', '<', today + timedelta(days=1))
        ], order='check_in desc')
        
        today_hours = sum(att.worked_hours for att in today_attendances if att.worked_hours)
        
        # Get recent attendance (last 5 records)
        recent_attendances = request.env['hr.attendance'].search([
            ('employee_id', '=', employee.id)
        ], limit=5, order='check_in desc')
        
        # Format recent attendances for display
        recent_display = [att.get_portal_display_data() for att in recent_attendances]
        
        # Get weekly and monthly stats
        weekly_hours = employee.get_weekly_hours()
        monthly_hours = employee.get_monthly_hours()
        
        values = self._prepare_portal_layout_values()
        values.update({
            'employee': employee,
            'status_info': status_info,
            'today_hours': today_hours,
            'weekly_hours': weekly_hours,
            'monthly_hours': monthly_hours,
            'recent_attendances': recent_display,
            'page_name': 'attendance_dashboard',
            'default_url': '/my/attendance',
        })
        
        return request.render('portal_hr_attendance.portal_attendance_dashboard', values)

    @http.route(['/my/attendance/history', '/my/attendance/history/page/<int:page>'], type='http', auth="user")
    def portal_attendance_history(self, page=1, date_from=None, date_to=None, sortby=None, search=None, **kw):
        """Attendance history with filtering"""
        try:
            employee = request.env['hr.employee'].get_portal_employee()
        except (UserError, ValidationError) as e:
            return request.render('portal_hr_attendance.portal_no_access', {'error_message': str(e)})

        # Default date range (last 30 days)
        if not date_from:
            date_from = (fields.Date.today() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not date_to:
            date_to = fields.Date.today().strftime('%Y-%m-%d')

        # Search domain
        domain = [
            ('employee_id', '=', employee.id),
            ('check_in', '>=', date_from + ' 00:00:00'),
            ('check_in', '<=', date_to + ' 23:59:59')
        ]

        # Sorting options
        searchbar_sortings = {
            'date': {'label': _('Date'), 'order': 'check_in desc'},
            'duration': {'label': _('Duration'), 'order': 'worked_hours desc'},
        }
        
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']

        # Count total records
        attendance_count = request.env['hr.attendance'].search_count(domain)
        
        # Pager
        pager = portal_pager(
            url="/my/attendance/history",
            url_args={'date_from': date_from, 'date_to': date_to, 'sortby': sortby},
            total=attendance_count,
            page=page,
            step=self._items_per_page
        )

        # Get attendances
        attendances = request.env['hr.attendance'].search(
            domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        
        # Format for display
        attendance_display = [att.get_portal_display_data() for att in attendances]
        
        # Summary stats for the period
        summary = employee.get_attendance_summary(date_from, date_to)

        values = self._prepare_portal_layout_values()
        values.update({
            'employee': employee,
            'attendances': attendance_display,
            'summary': summary,
            'page_name': 'attendance_history',
            'pager': pager,
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'date_from': date_from,
            'date_to': date_to,
            'default_url': '/my/attendance/history',
        })
        
        return request.render('portal_hr_attendance.portal_attendance_history', values)

    @http.route(['/my/attendance/export'], type='http', auth="user")
    def export_attendance(self, format='csv', date_from=None, date_to=None, **kw):
        """Export attendance data"""
        try:
            employee = request.env['hr.employee'].get_portal_employee()
        except (UserError, ValidationError):
            return request.redirect('/my/attendance')

        # Default date range if not provided
        if not date_from:
            date_from = (fields.Date.today() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not date_to:
            date_to = fields.Date.today().strftime('%Y-%m-%d')

        # Get export data
        export_data = request.env['hr.attendance'].get_attendance_for_export(
            employee.id, date_from, date_to, format)

        if format == 'csv':
            # Create CSV
            output = StringIO()
            writer = csv.DictWriter(output, fieldnames=['date', 'check_in', 'check_out', 'worked_hours', 'status'])
            writer.writeheader()
            writer.writerows(export_data)
            
            csv_data = output.getvalue()
            output.close()
            
            filename = f'attendance_{employee.name}_{date_from}_{date_to}.csv'
            
            return request.make_response(
                csv_data,
                headers=[
                    ('Content-Type', 'text/csv'),
                    ('Content-Disposition', f'attachment; filename="{filename}"')
                ]
            )

        return request.redirect('/my/attendance/history')

    @http.route(['/my/attendance/checkin'], type='json', auth="user")
    def portal_checkin(self, **kw):
        """Check-in via portal"""
        try:
            _logger.info("Portal check-in attempt by user %s", request.env.user.id)
            employee = request.env['hr.employee'].get_portal_employee()
            _logger.info("Employee found: %s (ID: %s)", employee.name, employee.id)
            
            # Check if already checked in
            last_attendance = request.env['hr.attendance'].search([
                ('employee_id', '=', employee.id)
            ], limit=1, order='check_in desc')
            
            if last_attendance and not last_attendance.check_out:
                _logger.warning("Employee %s already checked in", employee.name)
                return {'success': False, 'error': _('You are already checked in. Please check out first.')}
            
            # Create new attendance record
            attendance = request.env['hr.attendance'].create({
                'employee_id': employee.id,
                'check_in': fields.Datetime.now(),
            })
            _logger.info("Check-in successful for employee %s, attendance ID: %s", employee.name, attendance.id)
            
            return {
                'success': True, 
                'message': _('Successfully checked in at %s') % attendance.check_in.strftime('%H:%M'),
                'check_in_time': attendance.check_in.strftime('%Y-%m-%d %H:%M:%S')
            }
        except (UserError, ValidationError) as e:
            _logger.error("Portal check-in error for user %s: %s", request.env.user.id, str(e))
            return {'success': False, 'error': str(e)}
        except Exception as e:
            _logger.exception("Unexpected error during portal check-in for user %s", request.env.user.id)
            return {'success': False, 'error': _('An unexpected error occurred: %s') % str(e)}

    @http.route(['/my/attendance/checkout'], type='json', auth="user")
    def portal_checkout(self, **kw):
        """Check-out via portal"""
        try:
            employee = request.env['hr.employee'].get_portal_employee()
            
            # Find last check-in without check-out
            last_attendance = request.env['hr.attendance'].search([
                ('employee_id', '=', employee.id),
                ('check_out', '=', False)
            ], limit=1, order='check_in desc')
            
            if not last_attendance:
                return {'success': False, 'error': _('No active check-in found. Please check in first.')}
            
            # Set check-out time
            checkout_time = fields.Datetime.now()
            last_attendance.check_out = checkout_time
            
            return {
                'success': True,
                'message': _('Successfully checked out at %s') % checkout_time.strftime('%H:%M'),
                'check_out_time': checkout_time.strftime('%Y-%m-%d %H:%M:%S'),
                'worked_hours': last_attendance.worked_hours
            }
        except (UserError, ValidationError) as e:
            return {'success': False, 'error': str(e)}

    @http.route(['/my/attendance/emergency-checkout'], type='json', auth="user")
    def emergency_checkout(self, **kw):
        """Emergency check-out via AJAX"""
        try:
            employee = request.env['hr.employee'].get_portal_employee()
            result = employee.emergency_checkout()
            return {'success': True, 'data': result}
        except (UserError, ValidationError) as e:
            return {'success': False, 'error': str(e)}

    @http.route(['/my/attendance/stats'], type='json', auth="user")
    def get_attendance_stats(self, period='week', **kw):
        """Get attendance statistics via AJAX"""
        try:
            employee = request.env['hr.employee'].get_portal_employee()
            
            if period == 'week':
                hours = employee.get_weekly_hours()
            elif period == 'month':
                hours = employee.get_monthly_hours()
            else:
                hours = 0
                
            return {'success': True, 'hours': hours}
        except (UserError, ValidationError) as e:
            return {'success': False, 'error': str(e)}

    @http.route(['/my/attendance/status'], type='json', auth="user")
    def get_current_status(self, **kw):
        """Get current attendance status via AJAX"""
        try:
            employee = request.env['hr.employee'].get_portal_employee()
            status_info = employee.get_current_attendance_status()
            return {'success': True, 'data': status_info}
        except (UserError, ValidationError) as e:
            return {'success': False, 'error': str(e)}