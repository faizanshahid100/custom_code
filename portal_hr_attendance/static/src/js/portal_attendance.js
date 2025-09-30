/* Portal Attendance JavaScript */

odoo.define('portal_hr_attendance.portal', function (require) {
    'use strict';

    var publicWidget = require('web.public.widget');
    var ajax = require('web.ajax');
    var core = require('web.core');
    
    var _t = core._t;

    // Main Portal Attendance Widget
    var PortalAttendanceWidget = publicWidget.Widget.extend({
        selector: '.o_portal_wrap',
        events: {
            'click #emergencyCheckoutBtn': '_onEmergencyCheckout',
            'click .refresh-status': '_onRefreshStatus',
            'change .date-filter': '_onDateFilterChange',
            'click .export-btn': '_onExportClick',
        },

        start: function () {
            this._super.apply(this, arguments);
            this._initializeTooltips();
            this._startAutoRefresh();
            this._initializeDatePickers();
            return Promise.resolve();
        },

        // Initialize tooltips
        _initializeTooltips: function () {
            this.$('[data-toggle="tooltip"]').tooltip();
        },

        // Initialize date pickers
        _initializeDatePickers: function () {
            // Set default date values if not set
            var today = new Date();
            var thirtyDaysAgo = new Date(today.getTime() - (30 * 24 * 60 * 60 * 1000));
            
            if (!this.$('#date_from').val()) {
                this.$('#date_from').val(this._formatDate(thirtyDaysAgo));
            }
            if (!this.$('#date_to').val()) {
                this.$('#date_to').val(this._formatDate(today));
            }
        },

        // Format date for input
        _formatDate: function (date) {
            return date.toISOString().split('T')[0];
        },

        // Auto-refresh status every 5 minutes
        _startAutoRefresh: function () {
            var self = this;
            if (this.$('.attendance-dashboard').length) {
                setInterval(function () {
                    self._refreshAttendanceStatus();
                }, 300000); // 5 minutes
            }
        },

        // Emergency checkout handler
        _onEmergencyCheckout: function (ev) {
            ev.preventDefault();
            var self = this;
            var $btn = $(ev.currentTarget);
            
            // Show confirmation dialog
            if (!confirm(_t('Are you sure you want to perform an emergency checkout? This action will be logged.'))) {
                return;
            }

            // Disable button and show loading
            $btn.prop('disabled', true);
            $btn.html('<span class="loading-spinner"></span> Processing...');

            ajax.jsonRpc('/my/attendance/emergency-checkout', 'call', {})
                .then(function (result) {
                    if (result.success) {
                        self._showAlert('success', result.data.message);
                        // Refresh the page after 2 seconds
                        setTimeout(function () {
                            window.location.reload();
                        }, 2000);
                    } else {
                        self._showAlert('danger', result.error || _t('An error occurred during emergency checkout.'));
                        $btn.prop('disabled', false);
                        $btn.html('<i class="fa fa-exclamation-triangle mr-2"></i>Emergency Check-Out');
                    }
                })
                .catch(function (error) {
                    console.error('Emergency checkout error:', error);
                    self._showAlert('danger', _t('Network error. Please try again.'));
                    $btn.prop('disabled', false);
                    $btn.html('<i class="fa fa-exclamation-triangle mr-2"></i>Emergency Check-Out');
                });
        },

        // Refresh attendance status
        _onRefreshStatus: function (ev) {
            ev.preventDefault();
            this._refreshAttendanceStatus();
        },

        // Refresh attendance status via AJAX
        _refreshAttendanceStatus: function () {
            var self = this;
            ajax.jsonRpc('/my/attendance/status', 'call', {})
                .then(function (result) {
                    if (result.success) {
                        self._updateStatusDisplay(result.data);
                    }
                })
                .catch(function (error) {
                    console.error('Status refresh error:', error);
                });
        },

        // Update status display
        _updateStatusDisplay: function (statusData) {
            var $statusBadge = this.$('.status-badge');
            var $lastActivity = this.$('.last-activity');
            var $emergencyBtn = this.$('#emergencyCheckoutBtn');

            // Update status badge
            if (statusData.status === 'checked_in') {
                $statusBadge.removeClass('badge-secondary').addClass('badge-success');
                $statusBadge.html('<i class="fa fa-clock mr-1"></i>' + statusData.status_text);
            } else {
                $statusBadge.removeClass('badge-success').addClass('badge-secondary');
                $statusBadge.html('<i class="fa fa-pause-circle mr-1"></i>' + statusData.status_text);
            }

            // Update last activity
            if (statusData.last_activity) {
                $lastActivity.text('Last activity: ' + this._formatDateTime(statusData.last_activity));
            }

            // Show/hide emergency checkout button
            if (statusData.can_emergency_checkout) {
                $emergencyBtn.show();
            } else {
                $emergencyBtn.hide();
            }
        },

        // Format datetime for display
        _formatDateTime: function (dateStr) {
            var date = new Date(dateStr);
            return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
        },

        // Date filter change handler
        _onDateFilterChange: function (ev) {
            var $form = $(ev.target).closest('form');
            if (this._validateDateRange($form)) {
                $form.submit();
            }
        },

        // Validate date range
        _validateDateRange: function ($form) {
            var dateFrom = new Date($form.find('#date_from').val());
            var dateTo = new Date($form.find('#date_to').val());
            
            if (dateFrom > dateTo) {
                this._showAlert('warning', _t('Start date cannot be later than end date.'));
                return false;
            }
            
            var diffTime = Math.abs(dateTo - dateFrom);
            var diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
            
            if (diffDays > 365) {
                this._showAlert('warning', _t('Date range cannot exceed 365 days.'));
                return false;
            }
            
            return true;
        },

        // Export button handler
        _onExportClick: function (ev) {
            var $btn = $(ev.currentTarget);
            $btn.prop('disabled', true);
            
            // Re-enable button after 3 seconds
            setTimeout(function () {
                $btn.prop('disabled', false);
            }, 3000);
            
            this._showAlert('info', _t('Export started. Download will begin shortly.'));
        },

        // Show alert messages
        _showAlert: function (type, message) {
            var alertClass = 'alert-' + type;
            var iconClass = type === 'success' ? 'fa-check-circle' : 
                           type === 'danger' ? 'fa-exclamation-circle' : 
                           type === 'warning' ? 'fa-exclamation-triangle' : 'fa-info-circle';
            
            var $alert = $('<div class="alert ' + alertClass + ' alert-dismissible fade show alert-custom" role="alert">' +
                          '<i class="fa ' + iconClass + ' mr-2"></i>' + message +
                          '<button type="button" class="close" data-dismiss="alert">' +
                          '<span aria-hidden="true">&times;</span>' +
                          '</button>' +
                          '</div>');
            
            // Insert at top of container
            this.$('.container').first().prepend($alert);
            
            // Auto-dismiss after 5 seconds
            setTimeout(function () {
                $alert.alert('close');
            }, 5000);
        },

        // Get attendance stats
        _getAttendanceStats: function (period) {
            return ajax.jsonRpc('/my/attendance/stats', 'call', { period: period });
        },
    });

    // Stats Update Widget
    var AttendanceStatsWidget = publicWidget.Widget.extend({
        selector: '.attendance-stats',
        events: {
            'click .stats-period': '_onPeriodClick',
        },

        start: function () {
            this._super.apply(this, arguments);
            this._updateStats();
            return Promise.resolve();
        },

        _onPeriodClick: function (ev) {
            var period = $(ev.currentTarget).data('period');
            this._updateStats(period);
        },

        _updateStats: function (period) {
            var self = this;
            period = period || 'week';
            
            ajax.jsonRpc('/my/attendance/stats', 'call', { period: period })
                .then(function (result) {
                    if (result.success) {
                        self._displayStats(result.hours, period);
                    }
                })
                .catch(function (error) {
                    console.error('Stats update error:', error);
                });
        },

        _displayStats: function (hours, period) {
            var $display = this.$('.stats-display');
            $display.text(hours.toFixed(1) + ' hours');
            
            // Update period indicator
            this.$('.stats-period').removeClass('active');
            this.$('.stats-period[data-period="' + period + '"]').addClass('active');
        },
    });

    // Real-time Clock Widget
    var AttendanceClockWidget = publicWidget.Widget.extend({
        selector: '.attendance-clock',

        start: function () {
            this._super.apply(this, arguments);
            this._startClock();
            return Promise.resolve();
        },

        _startClock: function () {
            var self = this;
            setInterval(function () {
                self._updateClock();
            }, 1000);
            this._updateClock();
        },

        _updateClock: function () {
            var now = new Date();
            var timeStr = now.toLocaleTimeString();
            var dateStr = now.toLocaleDateString();
            
            this.$('.current-time').text(timeStr);
            this.$('.current-date').text(dateStr);
        },
    });

    // Initialize widgets
    publicWidget.registry.PortalAttendanceWidget = PortalAttendanceWidget;
    publicWidget.registry.AttendanceStatsWidget = AttendanceStatsWidget;
    publicWidget.registry.AttendanceClockWidget = AttendanceClockWidget;

    return {
        PortalAttendanceWidget: PortalAttendanceWidget,
        AttendanceStatsWidget: AttendanceStatsWidget,
        AttendanceClockWidget: AttendanceClockWidget,
    };
});