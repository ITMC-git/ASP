from odoo import fields, models, api
from datetime import datetime, timedelta


class DailyReporting(models.Model):
    _name = "daily.reporting"
    _description = "Daily Reporting"

    date = fields.Date(store=True)
    employee_id = fields.Many2one("hr.employee")
    check_in = fields.Datetime()
    check_out = fields.Datetime()
    check_in_location = fields.Char()
    check_out_location = fields.Char()
    work_hours = fields.Float(compute="_compute_working_hours", store=True)
    is_not_working_day = fields.Boolean()
    holiday_id = fields.Many2one("hr.leave")
    is_late_check_in = fields.Boolean(compute="_compute_late_check_in", store=True)
    is_after_10_check_in = fields.Boolean(compute="_compute_after_10_check_in", store=True)
   

    @api.depends("check_in", "check_out")
    def _compute_working_hours(self):
        for rec in self:
            if rec.check_in and rec.check_out:
                duration = rec.check_out - rec.check_in
                rec.work_hours = duration.total_seconds() / 3600
            else:
                rec.work_hours = 0
    
    @api.depends("check_in")
    def _compute_after_10_check_in(self):
        for rec in self:
            if rec.check_in:
                check_in = fields.Datetime.context_timestamp(rec.with_context(tz='Asia/Tbilisi'), rec.check_in)
                rec.is_after_10_check_in = check_in.hour >= 10
                   
    @api.depends("check_in", "employee_id.resource_calendar_id.attendance_ids", "employee_id.resource_calendar_id.attendance_ids.hour_from")
    def _compute_late_check_in(self):
        for rec in self:
            if not rec.check_in:
                rec.is_late_check_in = False
            else:
                today = fields.Date.today()
                weekday = today.weekday()
                working_day = rec.employee_id.resource_calendar_id.attendance_ids.filtered(lambda x: int(x.dayofweek) == weekday)
                if working_day:
                    hour_from = min(working_day.mapped("hour_from"))
                    check_in = fields.Datetime.context_timestamp(rec.with_context(tz='Asia/Tbilisi'), rec.check_in)
                    rec.is_late_check_in = check_in.hour > hour_from
                else:
                    rec.is_late_check_in = False

    @api.model
    def record_first_check_in_and_last_check_out(self):
        today = fields.Date.today()
        employees = self.env["hr.employee"].search([])
        for employee in employees:
            attendances = self.env["hr.attendance"].search([("employee_id", "=", employee.id)])
            if attendances:
                first_check_in = attendances.search([
                    ("check_in", "!=", False),
                    ("check_in", ">=", today),
                    ("check_in", "<", today + timedelta(days=1)),
                    ("employee_id", "=", employee.id)
                ], limit=1, order="check_in asc").check_in
                last_check_in = attendances.search([
                    ("check_in", "!=", False),
                    ("check_in", ">=", today),
                    ("check_in", "<", today + timedelta(days=1)),
                    ("employee_id", "=", employee.id)
                ], limit=1, order="check_in desc").check_in
                first_check_out = attendances.search([
                    ("check_out", "!=", False),
                    ("check_out", ">=", today),
                    ("check_out", "<", today + timedelta(days=1)),
                    ("employee_id", "=", employee.id)
                ], limit=1, order="check_out asc").check_out
                last_check_out = attendances.search([
                    ("check_out", "!=", False),
                    ("check_out", ">=", today),
                    ("check_out", "<", today + timedelta(days=1)),
                    ("employee_id", "=", employee.id)
                ], limit=1, order="check_out desc").check_out
                checks = []
                checks.append(first_check_in)
                checks.append(last_check_in)
                checks.append(first_check_out)
                checks.append(last_check_out)
                filtred_checks = [check for check in checks if check != False]
                if len(filtred_checks) != 0:
                    check_in = self.process_check_in_and_check_out(
                        filtred_checks)["check_in"]
                    check_out = self.process_check_in_and_check_out(
                    filtred_checks)["check_out"]
                    daily_reports = self.env["daily.reporting"].search([
                        ("employee_id", "=", employee.id),
                        ("date", "=", today),
                        ("check_in", "=", check_in),
                        ("check_out", "=", check_out),
                    ])
                    if not daily_reports:
                        existing_reports = self.env["daily.reporting"].search([
                            ("date", "=", today),
                            ("employee_id", "=", employee.id)
                        ])
                        if existing_reports:
                            if check_in != check_out:
                                existing_reports.write({
                                    "check_in": check_in,
                                    "check_out": check_out,
                                })
                            else:
                                existing_reports.write({
                                    "check_in": check_in,
                                })
                        elif check_in != check_out:
                            self.env["daily.reporting"].create({
                                "date": check_in.date(),
                                "employee_id": employee.id,
                                "check_in": check_in,
                                "check_out": check_out,
                            })
                        else:
                            self.env["daily.reporting"].create({
                                "date": check_in.date(),
                                "employee_id": employee.id,
                                "check_in": check_in,
                                "check_out": False,
                            })
                    else:
                        if check_in != check_out:
                            daily_reports.write({
                                "check_in": check_in,
                                "check_out": check_out,
                            })
                        else:
                            daily_reports.write({
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
            weekday = today.weekday()
            working_day = employee.resource_calendar_id.attendance_ids.filtered(lambda x: int(x.dayofweek) == weekday)
            existing_attendance = self.env["hr.attendance"].search([
                ("employee_id", "=", employee.id),
                ("check_in", ">=", today),  
                ("check_in", "<", today + timedelta(days=1)),  
            ])
            if not existing_attendance:
                daily_reporting = self.env["daily.reporting"].search([
                    ("date", "=", today),
                    ("employee_id", "=", employee.id),
                ])
                if not daily_reporting:
                    approved_leave = self.env["hr.leave"].search([
                        ("employee_id", "=", employee.id),
                        ("state", "=", "validate"),
                        ("request_date_from", "<=", today),
                        ("request_date_to", ">=", today),
                    ], limit=1)
                    if not working_day:
                        self.env["daily.reporting"].create({
                            "date": today,
                            "employee_id": employee.id,
                            "is_not_working_day": True,
                        })
                
                    elif approved_leave:
                        self.env["daily.reporting"].create({
                            "date": today,
                            "employee_id": employee.id,
                            "is_not_working_day": True,
                            "holiday_id": approved_leave.id,
                        })
                    else:
                        self.env["daily.reporting"].create({
                            "date": today,
                            "employee_id": employee.id,
                        })
    
    @api.model
    def create_daily_reporting_march_records(self):
        first_check_in = '2024-03-01'
        last_check_in = '2024-04-01'
        march_attendance = self.env["hr.attendance"].search([
            ("check_in", ">=", first_check_in),
            ("check_in", "<", last_check_in)
        ])
        if march_attendance:
            for attendance_record in march_attendance:
                self.env['daily.reporting'].create({
                    "date": attendance_record.check_in.date(),
                    "employee_id": attendance_record.employee_id.id,
                    "check_in": attendance_record.check_in,
                    "check_out": attendance_record.check_out,
                })
        