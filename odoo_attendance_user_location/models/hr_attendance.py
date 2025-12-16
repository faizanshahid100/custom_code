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

    # @api.model
    # def create(self, vals):
    #     # 1. Detect OS from user agent if available
    #     try:
    #         user_agent = request.httprequest.headers.get('User-Agent', '')
    #         if "Windows" in user_agent:
    #             vals['os'] = "Windows"
    #         elif "Mac" in user_agent:
    #             vals['os'] = "MacOS"
    #         elif "Android" in user_agent:
    #             vals['os'] = "Android"
    #         elif "iPhone" in user_agent or "iPad" in user_agent:
    #             vals['os'] = "iOS"
    #         elif "Linux" in user_agent:
    #             vals['os'] = "Linux"
    #         else:
    #             vals['os'] = "Unknown"
    #     except Exception as e:
    #         _logger.warning(f"Could not determine OS: {e}")
    #
    #     # 2. Detect Address from Latitude/Longitude if present
    #     lat = vals.get('checkin_latitude')
    #     lon = vals.get('checkin_longitude')
    #
    #     try:
    #         if lat and lon:
    #             url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}"
    #             headers = {
    #                 'User-Agent': 'Odoo Attendance',
    #                 'Accept-Language': 'en'  # Force response in English
    #             }
    #             response = requests.get(url, headers=headers)
    #             if response.ok:
    #                 data = response.json()
    #                 address = data.get('address', {}).get('district') or \
    #                           data.get('address', {}).get('town') or \
    #                           data.get('address', {}).get('village')
    #                 if address:
    #                     vals['address'] = address
    #     except Exception as e:
    #         _logger.warning(f"Could not determine address from lat/lon: {e}")
    #
    #     return super(HrAttendances, self).create(vals)
    #
    # def write(self, vals):
    #     # Check if check-out is happening
    #     if 'check_out' in vals:
    #         try:
    #             # Append OS info
    #             user_agent = request.httprequest.headers.get('User-Agent', '')
    #             new_os = "Unknown"
    #             if "Windows" in user_agent:
    #                 new_os = "Windows"
    #             elif "Mac" in user_agent:
    #                 new_os = "MacOS"
    #             elif "Android" in user_agent:
    #                 new_os = "Android"
    #             elif "iPhone" in user_agent or "iPad" in user_agent:
    #                 new_os = "iOS"
    #             elif "Linux" in user_agent:
    #                 new_os = "Linux"
    #
    #             for record in self:
    #                 # Append to existing OS
    #                 if record.os:
    #                     vals['os'] = f"{record.os}/{new_os}"
    #                 else:
    #                     vals['os'] = new_os
    #
    #                 # Append to existing address
    #                 lat = vals.get('checkout_latitude') or record.checkout_latitude
    #                 lon = vals.get('checkout_longitude') or record.checkout_longitude
    #                 if lat and lon:
    #                     url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}"
    #                     headers = {
    #                         'User-Agent': 'Odoo Attendance',
    #                         'Accept-Language': 'en'
    #                     }
    #                     response = requests.get(url, headers=headers)
    #                     if response.ok:
    #                         data = response.json()
    #                         new_address = data.get('address', {}).get('district') or \
    #                                       data.get('address', {}).get('town') or \
    #                                       data.get('address', {}).get('village')
    #                         if new_address:
    #                             if record.address:
    #                                 vals['address'] = f"{record.address}/{new_address}"
    #                             else:
    #                                 vals['address'] = new_address
    #         except Exception as e:
    #             _logger.warning(f"Could not append OS or address: {e}")
    #
    #     return super(HrAttendances, self).write(vals)