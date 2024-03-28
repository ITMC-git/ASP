from odoo import fields, models, api
from datetime import datetime, timedelta


class DailyReporting(models.Model):
    _name = "daily.reporting"
    _description = "Daily Reporting"
    _inherit = ['resource.mixin']

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
        records = self.env["daily.reporting"]
        hr_attendance_model = self.env["hr.attendance"]
        attendance_today = hr_attendance_model.search(["|", 
        ("check_in", "<=", today),("check_out", "<=", today),
        "|",
        ("check_out", ">=", today - timedelta(days=1)),
        ("check_in", ">=", today - timedelta(days=1)),
        ])
        employees = self.env["hr.employee"].search([])
        for employee in employees:
            existing_attendance = attendance_today.filtered(lambda x: x.employee_id.id == employee.id)
            check_ins = existing_attendance.mapped("check_in")
            check_outs = existing_attendance.mapped("check_out")
            checks = check_ins + check_outs
            filtered_checks = [check for check in checks if check != False]
            filtered_checks_f = f"checks {filtered_checks}"
            first_check_in = min(filtered_checks)
            last_check_out = max(filtered_checks)
            check_in_f = f"check in {first_check_in}"
            check_out_f = f"check out {last_check_out}"
            weekday = today.weekday()
            test = employee.resource_calendar_id.attendance_ids.search([
                ("dayofweek", "=", weekday)
            ],limit=1)

            resources = self.env["resource.mixin"]
            leaves = resources._get_leave_days_data_batch(first_check_in, last_check_out)
            leaves_f = f"leaves {leaves}"
            if first_check_in.date() == last_check_out.date():
                today_records = records.search(["|",
                    ("check_in", "<=", today),("check_out", "<=", today),
                    "|",
                    ("check_out", ">=", today - timedelta(days=1)),
                    ("check_in", ">=", today - timedelta(days=1)),])
                if today_records:
                    for rec in today_records:
                        rec.check_in = first_check_in
                        rec.check_out = last_check_out
                else:
                    if not test:
                        records.create({
                            "employee_id": employee,
                            "check_in": first_check_in,
                            "check_out": last_check_out,
                            "is_not_working_day": True
                        })
                    else:
                        records.create({
                            "employee_id": employee,
                            "check_in": first_check_in,
                            "check_out": last_check_out,
                        })

     
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
