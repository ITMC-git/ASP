from odoo import fields, models, api
from datetime import datetime, timedelta


class DailyReporting(models.Model):
    _name = "daily.reporting"
    _description = "Daily Reporting"

    date = fields.Date(default=fields.Date.today())
    employee_id = fields.Many2one("hr.employee")
    check_in = fields.Datetime()
    check_out = fields.Datetime()
    work_hours = fields.Float(compute="_compute_working_hours")
    is_not_working_day = fields.Boolean()
    holiday_id = fields.Many2one("hr.leave")

    @api.depends("check_in", "check_out")
    def _compute_working_hours(self):
        for rec in self:
            if rec.check_in and rec.check_out:
                duration = rec.check_out - rec.check_in
                rec.work_hours = duration.total_seconds() / 3600
            else:
                rec.work_hours = 0

    @api.model
    def record_first_check_in_and_last_check_out(self):
        employees = self.env["hr.employee"].search([])
        employee_test = self.env["hr.employee"].browse(2)
        attendances = self.env["hr.attendance"].search([("employee_id", "=", employee_test.id)])
        date_string = "03/20/2024 00:00:00"
        date_object = datetime.strptime(date_string, "%m/%d/%Y %H:%M:%S")
        first_check_in = attendances.search([
            ("check_in", "!=", False),
            ("check_in", ">=", date_object),
            ("employee_id", "=", employee_test.id)
        ], limit=1, order="check_in asc").check_in
        last_check_in = attendances.search([
            ("check_in", "!=", False),
            ("check_in", "<=", date_object + timedelta(days=1)),
            ("employee_id", "=", employee_test.id)
        ], limit=1, order="check_in desc").check_in
        first_check_out = attendances.search([
            ("check_out", "!=", False),
            ("check_out", ">=", date_object),
            ("employee_id", "=", employee_test.id)
        ], limit=1, order="check_out asc").check_out
        last_check_out = attendances.search([
            ("check_out", "!=", False),
            ("check_out", "<=", date_object + timedelta(days=1)),
            ("employee_id", "=", employee_test.id)
        ], limit=1, order="check_out desc").check_out

        check_in = self.process_check_in_and_check_out(
            first_check_in,
            last_check_in,
            first_check_out,
            last_check_out)["check_in"]
        check_out = self.process_check_in_and_check_out(
            first_check_in,
            last_check_in,
            first_check_out,
            last_check_out)["check_out"]

        self.env["daily.reporting"].create({
            "employee_id": employee_test.id,
            "check_in": check_in,
            "check_out": check_out,
        })

    def process_check_in_and_check_out(self, first_check_in, last_check_in, first_check_out, last_check_out):
        # The least date is the check in the most date is the check out
        check_in = min(first_check_in, last_check_in, first_check_out, last_check_out)
        check_out = max(first_check_in, last_check_in, first_check_out, last_check_out)
        return {
            "check_in": check_in,
            "check_out": check_out
        }

    @api.model
    def create_unchecked_daily_reporting_records(self):
        today = fields.Date.today()
        employees = self.env["hr.employee"].search([])
        for employee in employees:
            checked_attendance = self.env["hr.attendance"].search([
                ("employee_id", "=", employee.id),
                "|", ("check_in", "!=", False),
                ("check_out", "!=", False),
                ("date", "<=", today)
            ])
            weekday = today.weekday()
            weekday -= 1
            weekday_f = f"weekday {weekday}"
            test = employee.resource_calendar_id.attendance_ids.search([
                ("dayofweek", "=", weekday)
            ],limit=1)
            if not test:
                if not checked_attendance:
                    self.env["daily.reporting"].create({
                        "employee_id": employee.id,
                        "is_not_working_day": True,
                    })
            else:
                 if not checked_attendance:
                    self.env["daily.reporting"].create({
                        "employee_id": employee.id,
                    })
