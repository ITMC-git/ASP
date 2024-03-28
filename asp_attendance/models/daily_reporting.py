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
        today = fields.Date.today()
        employees = self.env["hr.employee"].search([])
        for employee in employees:
            attendances = self.env["hr.attendance"].search([("employee_id", "=", employee.id)])
            first_check_in = attendances.search([
                ("check_in", "!=", False),
                ("check_in", ">=", today),
                ("employee_id", "=", employee.id)
            ], limit=1, order="check_in asc").check_in
            last_check_in = attendances.search([
                ("check_in", "!=", False),
                ("check_in", "<=", today + timedelta(days=1)),
                ("employee_id", "=", employee.id)
            ], limit=1, order="check_in desc").check_in
            first_check_out = attendances.search([
                ("check_out", "!=", False),
                ("check_out", ">=", today),
                ("employee_id", "=", employee.id)
            ], limit=1, order="check_out asc").check_out
            last_check_out = attendances.search([
                ("check_out", "!=", False),
                ("check_out", "<=", today + timedelta(days=1)),
                ("employee_id", "=", employee.id)
            ], limit=1, order="check_out desc").check_out
            checks = []
            checks.append(first_check_in)
            checks.append(last_check_in)
            checks.append(first_check_out)
            checks.append(last_check_out)
            filtred_checks = [check for check in checks if check != False]
            check_in = self.process_check_in_and_check_out(
                filtred_checks)["check_in"]
            check_out = self.process_check_in_and_check_out(
               filtred_checks)["check_out"]
            daily_reports = self.env["daily.reporting"].search(["|",
                ("check_in", "=", check_in),
                ("check_out", "=", check_out),
            ])
            if not daily_reports:
                if check_in != check_out:
                    self.env["daily.reporting"].create({
                        "employee_id": employee.id,
                        "check_in": check_in,
                        "check_out": check_out,
                    })
                else:
                    self.env["daily.reporting"].create({
                        "employee_id": employee.id,
                        "check_in": check_in,
                        "check_out": False,
                    })
            else:
                if check_in != check_out:
                    daily_reports.write({
                        "employee_id": employee.id,
                        "check_in": check_in,
                        "check_out": check_out,
                    })
                else:
                    daily_reports.write({
                        "employee_id": employee.id,
                        "check_in": check_in,
                    })

    def process_check_in_and_check_out(self, filtred_checks):
        # The least date is the check in the most date is the check out
        check_in = min(filtred_checks)
        check_out = max(filtred_checks)
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
