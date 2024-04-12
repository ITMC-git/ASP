from odoo import fields, models, _
from odoo.exceptions import UserError


class AspUpdateDailyReport(models.TransientModel):
    _name = "asp.update.daily.report"
    _description = "Update daily report"

    date = fields.Date(string="Date")

    def action_apply(self):
        self.env["daily.reporting"].create_daily_report(self.date)
