from odoo import fields, models, _ , api
from odoo.exceptions import ValidationError



class AspUpdateDailyReport(models.TransientModel):
    _name = "asp.update.daily.report"
    _description = "Update daily report"

    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)

    @api.constrains("date_from", "date_to")
    def _check_dates(self):
        for rec in self:
            today = fields.Date.today()
            if rec.date_from and rec.date_from and rec.date_from > rec.date_to:
                raise ValidationError(_("Start date must be lower than end date."))
            elif rec.date_from > today or rec.date_to > today:
                raise ValidationError(_("Enter the current or previous dates"))
             
    def action_apply(self):
        self.env["daily.reporting"].create_daily_report(self.date_from, self.date_to)
       