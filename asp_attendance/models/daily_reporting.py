from odoo import fields, models, api
from datetime import timedelta, datetime, time
import pytz

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
        tz = pytz.timezone('Asia/Tbilisi')  # Assuming the timezone of the attendance records

        # Convert today to the user's timezone
        today_tz = tz.localize(datetime.combine(today, time.min))

        for attendance in attendances:
            check_in = attendance.check_in
            check_out = attendance.check_out

            # Check if the date component of check_in and check_out matches today
            if check_in and check_in.date() == today_tz.date():
                # Append a tuple of (check_in time, location) to attendance_data
                attendance_data.append((check_in, attendance.check_in_location))

            if check_out and check_out.date() == today_tz.date():
                # Append a tuple of (check_out time, location) to attendance_data
                attendance_data.append((check_out, attendance.check_out_location))

        return attendance_data
       
    @api.model
    def _not_working_day_or_leave(self, employee, date):
        """ Check if a date is not a working day or a leave. """
   
        weekday = date.weekday()
        working_day = employee.resource_calendar_id.attendance_ids.filtered(
            lambda x: int(x.dayofweek) == weekday)
        leave = employee.resource_calendar_id.leave_ids.filtered(
            lambda x: x.date_from.date() <= date.date() and x.date_to.date() >= date.date())
        if leave.holiday_id:
            leave = leave.filtered(lambda x: x.holiday_id.employee_id == employee)
        return {
            "not_working_day": bool(not working_day or leave),
            "leave": leave
        }
    
    @api.model
    def create_daily_report(self, date_from=None, date_to=None):
        tz = pytz.timezone('Asia/Tbilisi')
        date_from = date_from or fields.Date.today()
        date_to = date_to or date_from
        employees = self.env["hr.employee"].search([])

        date_from_tz = tz.localize(datetime.combine(date_from, time.min))
        date_from_utc = date_from_tz.astimezone(pytz.utc)
        date_to_tz = tz.localize(datetime.combine(date_to, time.min))
        date_to_utc = date_to_tz.astimezone(pytz.utc)

        for employee in employees:
            # Get today's attendances
            days = (date_to_tz - date_from_tz).days
            current_date = date_from_tz
            curent_date_from = date_from_utc
            for _ in range(0, days+1):
                tomorrow = curent_date_from + timedelta(days=1)
                attendances = self.env["hr.attendance"].search([
                    ("employee_id", "=", employee.id),
                    "|",
                    "&",
                    ("check_in", ">=", curent_date_from),
                    ("check_in", "<", tomorrow),
                    "&",
                    ("check_out", ">=", curent_date_from),
                    ("check_out", "<", tomorrow),
                ])
                daily_report = self.search([("date", "=", current_date), ("employee_id", "=", employee.id)])
                not_working_day_or_leave = self._not_working_day_or_leave(employee, current_date)
                is_not_working_day = not_working_day_or_leave["not_working_day"]
                leave = not_working_day_or_leave["leave"] if not_working_day_or_leave["leave"].holiday_id else False
               
                if not daily_report:
                    daily_report = self.create({
                        "date": current_date,
                        "employee_id": employee.id,
                        "is_not_working_day": is_not_working_day,
                        "holiday_id":  leave.holiday_id.id if leave else False,
                    })

                if attendances:
                    attendance_data = self._get_attendance_data(attendances, current_date)
                    check_in, check_in_location = min(attendance_data, key=lambda x: x[0])
                    check_out, check_out_location = max(attendance_data, key=lambda x: x[0])
                    if check_out > check_in:
                        difference = (check_out - check_in).total_seconds() / 60
                    else:
                        difference = 0
                    daily_report.update({
                        "check_in": check_in,
                        "check_out": check_out if difference > 1 else None,
                        "check_in_location": check_in_location,
                        "check_out_location": check_out_location if difference > 1 else False
                    })

                daily_report.update({
                    "is_not_working_day": is_not_working_day,
                    "holiday_id":  leave.holiday_id.id if leave else False,
                })
                current_date += timedelta(days=1)
                curent_date_from += timedelta(days=1)
