from odoo import fields, models, _
from odoo.exceptions import UserError


class AspUpdateDailyReport(models.TransientModel):
    _name = "asp.update.daily.report"
    _description = "Update daily report"

    date_from = fields.Date(string="From")
    date_to = fields.Date(string="To")


    def action_apply(self):
        self.env["daily.reporting"].create_daily_report(self.date_from)
