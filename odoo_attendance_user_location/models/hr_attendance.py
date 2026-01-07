# -*- coding: utf-8 -*-
from odoo import fields, models, api
import logging
import requests
import re
from odoo.http import request

_logger = logging.getLogger(__name__)


class HrAttendances(models.Model):
    """Inherits HR Attendance model"""
    _inherit = 'hr.attendance'

    checkin_address = fields.Char(string='Check In Address', store=True,
                                  help="Check in address of the User")
    checkout_address = fields.Char(string='Check Out Address', store=True,
                                   help="Check out address of the User")
    checkin_latitude = fields.Char(string='Check In Latitude', store=True,
                                   help="Check in latitude of the User")
    checkout_latitude = fields.Char(string='Check Out Latitude', store=True,
                                    help="Check out latitude of the User")
    checkin_longitude = fields.Char(string='Check In Longitude', store=True,
                                    help="Check in longitude of the User")
    checkout_longitude = fields.Char(string='Check Out Longitude', store=True,
                                     help="Check out longitude of the User")
    checkin_location = fields.Char(string='Check In Location Link', store=True,
                                   help="Check in location link of the User")
    checkout_location = fields.Char(string='Check Out Location Link', store=True,
                                    help="Check out location link of the User")
    is_onsite_in = fields.Boolean('On-Site In')
    is_onsite_out = fields.Boolean('On-Site Out')
    os = fields.Char('OS')
    address = fields.Char('Address')

    @api.model
    def create(self, vals):
        company = self.env.company
        is_onsite = False

        try:
            public_ip = requests.get(
                "https://api.ipify.org",
                timeout=3
            ).text.strip()
            print(public_ip)

            office_ips = [
                company.work_from_office_ip_1,
                company.work_from_office_ip_2,
            ]
            print(office_ips)

            # Clean & compare
            office_ips = [ip.strip() for ip in office_ips if ip]

            if public_ip in office_ips:
                is_onsite = True

        except Exception as e:
            _logger.warning(f"Could not determine public IP: {e}")
            print('Errrrrorrrrr')

        vals['is_onsite_in'] = is_onsite

        return super().create(vals)
