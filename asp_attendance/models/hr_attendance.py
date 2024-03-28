from odoo import fields, models


class HRAttendance(models.Model):
    _inherit = "hr.attendance"

    date = fields.Date(default=fields.Date.today())