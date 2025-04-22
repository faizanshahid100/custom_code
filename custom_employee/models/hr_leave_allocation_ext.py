# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from collections import defaultdict
from odoo.tools.date_utils import get_timedelta
import logging

_logger = logging.getLogger(__name__)

class HrLeaveAllocation(models.Model):
    _inherit = 'hr.leave.allocation'


    def _process_accrual_plans(self, date_to=False, force_period=False):
        """
        This method is part of the cron's process.
        The goal of this method is to retroactively apply accrual plan levels and progress from nextcall to date_to or today.
        If force_period is set, the accrual will run until date_to in a prorated way (used for end of year accrual actions).
        """
        date_to = date_to or fields.Date.today()
        first_allocation = _("""This allocation have already ran once, any modification won't be effective to the days allocated to the employee. If you need to change the configuration of the allocation, cancel and create a new one.""")
        for allocation in self:
            if allocation.employee_id.is_probation:
                continue
            level_ids = allocation.accrual_plan_id.level_ids.sorted('sequence')
            if not level_ids:
                continue
            if not allocation.nextcall:
                first_level = level_ids[0]
                first_level_start_date = allocation.date_from + get_timedelta(first_level.start_count, first_level.start_type)
                if date_to < first_level_start_date:
                    # Accrual plan is not configured properly or has not started
                    continue
                allocation.lastcall = max(allocation.lastcall, first_level_start_date)
                allocation.nextcall = first_level._get_next_date(allocation.lastcall)
                if len(level_ids) > 1:
                    second_level_start_date = allocation.date_from + get_timedelta(level_ids[1].start_count, level_ids[1].start_type)
                    allocation.nextcall = min(second_level_start_date, allocation.nextcall)
                allocation._message_log(body=first_allocation)
            days_added_per_level = defaultdict(lambda: 0)
            while allocation.nextcall <= date_to:
                (current_level, current_level_idx) = allocation._get_current_accrual_plan_level_id(allocation.nextcall)
                if not current_level:
                    break
                current_level_maximum_leave = current_level.maximum_leave if current_level.added_value_type == "days" else current_level.maximum_leave / (allocation.employee_id.sudo().resource_id.calendar_id.hours_per_day or HOURS_PER_DAY)
                nextcall = current_level._get_next_date(allocation.nextcall)
                # Since _get_previous_date returns the given date if it corresponds to a call date
                # this will always return lastcall except possibly on the first call
                # this is used to prorate the first number of days given to the employee
                period_start = current_level._get_previous_date(allocation.lastcall)
                period_end = current_level._get_next_date(allocation.lastcall)
                # Also prorate this accrual in the event that we are passing from one level to another
                if current_level_idx < (len(level_ids) - 1) and allocation.accrual_plan_id.transition_mode == 'immediately':
                    next_level = level_ids[current_level_idx + 1]
                    current_level_last_date = allocation.date_from + get_timedelta(next_level.start_count, next_level.start_type)
                    if allocation.nextcall != current_level_last_date:
                        nextcall = min(nextcall, current_level_last_date)
                # We have to check for end of year actions if it is within our period
                #  since we can create retroactive allocations.
                if allocation.lastcall.year < allocation.nextcall.year and\
                    current_level.action_with_unused_accruals == 'postponed' and\
                    current_level.postpone_max_days > 0:
                    # Compute number of days kept
                    allocation_days = allocation.number_of_days - allocation.leaves_taken
                    allowed_to_keep = max(0, current_level.postpone_max_days - allocation_days)
                    number_of_days = min(allocation_days, current_level.postpone_max_days)
                    allocation.number_of_days = number_of_days + allocation.leaves_taken
                    total_gained_days = sum(days_added_per_level.values())
                    days_added_per_level.clear()
                    days_added_per_level[current_level] = min(total_gained_days, allowed_to_keep)
                gained_days = allocation._process_accrual_plan_level(
                    current_level, period_start, allocation.lastcall, period_end, allocation.nextcall)
                days_added_per_level[current_level] += gained_days
                if current_level_maximum_leave > 0 and sum(days_added_per_level.values()) > current_level_maximum_leave:
                    days_added_per_level[current_level] -= sum(days_added_per_level.values()) - current_level_maximum_leave

                allocation.lastcall = allocation.nextcall
                allocation.nextcall = nextcall
                if force_period and allocation.nextcall > date_to:
                    allocation.nextcall = date_to
                    force_period = False

            if days_added_per_level:
                number_of_days_to_add = allocation.number_of_days + sum(days_added_per_level.values())
                max_allocation_days = current_level_maximum_leave + (allocation.leaves_taken if allocation.type_request_unit != "hour" else allocation.leaves_taken / (allocation.employee_id.sudo().resource_id.calendar_id.hours_per_day or HOURS_PER_DAY))
                # Let's assume the limit of the last level is the correct one
                allocation.number_of_days = min(number_of_days_to_add, max_allocation_days) if current_level_maximum_leave > 0 else number_of_days_to_add
