from odoo import fields, models


class Employee(models.Model):
    _inherit = "hr.employee"

    asp_employee_id = fields.Char(
        string="ASP Employee ID",
        help="Employee ID from ASP Database.",
        groups="hr.group_hr_user",
    )
