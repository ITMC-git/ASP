from odoo import fields, models, api
from datetime import timedelta


class DailyReporting(models.Model):
    _name = "daily.reporting"
    _description = "Daily Reporting"

    date = fields.Date()
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
    def _get_attendance_data(self, attendances, today):
        attendance_data = []
        for attendance in attendances:
            check_in = attendance.check_in
            check_out = attendance.check_out

            if check_in and check_in.date() == today:
                attendance_data.append(check_in)

            if check_out and check_out.date() == today:
                attendance_data.append(check_out)
        return attendance_data

    @api.model
    def _not_working_day_or_leave(self, employee, date):
        """ Check if a date is not a working day or a leave. """
        weekday = date.weekday()
        working_day = employee.resource_calendar_id.attendance_ids.filtered(
            lambda x: int(x.dayofweek) == weekday)
        leave = employee.resource_calendar_id.leave_ids.filtered(
            lambda x: x.date_from.date() == date)
        return {
            "not_working_day": bool(not working_day or leave),
            "leave": leave
        }

    @api.model
    def create_daily_report(self, date=None):
        today = date or fields.Date.today()
        tomorrow = today + timedelta(days=1)
        employees = self.env["hr.employee"].search([])

        for employee in employees:
            # Get today's attendances
            attendances = self.env["hr.attendance"].search([
                ("employee_id", "=", employee.id),
                "|",
                "&",
                ("check_in", ">=", today),
                ("check_in", "<", tomorrow),
                "&",
                ("check_out", ">=", today),
                ("check_out", "<", tomorrow),
            ])
            daily_report = self.search([("date", "=", today), ("employee_id", "=", employee.id)])
            not_working_day_or_leave = self._not_working_day_or_leave(employee, today)
            is_not_working_day = not_working_day_or_leave["not_working_day"]
            leave = not_working_day_or_leave["leave"] if not_working_day_or_leave["leave"].holiday_id else False

            if not daily_report:
                daily_report = self.create({
                    "date": today,
                    "employee_id": employee.id,
                    "is_not_working_day": is_not_working_day,
                    "holiday_id": leave.holiday_id.id if leave else False,
                })

            if attendances:
                attendance_data = self._get_attendance_data(attendances, today)
                check_in = min(attendance_data)
                check_out = max(attendance_data)
                daily_report.update({
                    "check_in": check_in,
                    "check_out": check_out if check_out > check_in else None,
                })

            daily_report.update({
                "is_not_working_day": is_not_working_day,
                "holiday_id": leave.holiday_id.id if leave else False,
            })
