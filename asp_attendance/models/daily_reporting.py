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
    hours_to_work = fields.Float()
    schedule_difference = fields.Float(compute="_compute_schedule_differecne")
    change_reason = fields.Char()
    hour_from = fields.Float()
    hour_to = fields.Float()

    @api.depends("check_in", "check_out")
    def _compute_working_hours(self):
        tz = pytz.timezone('Asia/Tbilisi')
        for rec in self:
            if rec.check_in and rec.check_out and not rec.is_not_working_day:
                check_in = fields.Datetime.context_timestamp(
                    rec.with_context(tz='Asia/Tbilisi'),
                    rec.check_in,
                )
                check_out = fields.Datetime.context_timestamp(
                    rec.with_context(tz='Asia/Tbilisi'),
                    rec.check_out,
                )
                work_from = tz.localize(datetime(
                    check_in.year, check_in.month, check_in.day, int(rec.hour_from), 0, 0
                ))
                work_to = tz.localize(datetime(
                    check_in.year, check_in.month, check_in.day, int(rec.hour_to), 0, 0
                ))
                start_time = max(check_in, work_from)
                end_time = min(check_out, work_to)
                duration = end_time - start_time
                work_hours = duration.total_seconds() / 3600
                # Deduct 1 hour for a break
                if work_hours > 1:
                    work_hours -= 1
                # Cap worked hours to 8
                if work_hours > rec.hours_to_work:
                    work_hours = rec.hours_to_work
                rec.work_hours = work_hours
            else:
                rec.work_hours = 0.0

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

    @api.depends("hours_to_work", "check_in", "check_out")
    def _compute_schedule_differecne(self):
        '''
        Through this method, we determine the difference between the hours worked 
        and the hours in the schedule, but we also determine the tolerance for this time.
        '''
        overtime_company_threshold = self.env.company.overtime_company_threshold
        overtime_employee_threshold = self.env.company.overtime_employee_threshold
        #Convert to hours and change type to float
        tolerance_time_of_company_hours = float(overtime_company_threshold) / 60.0
        tolerance_time_of_employee_hours = float(overtime_employee_threshold) / 60.0
        for rec in self:
            if rec.hours_to_work and rec.check_in and rec.check_out:
                max_tolerance_time_of_compnay = rec.hours_to_work + tolerance_time_of_company_hours
                max_tolerance_time_of_employee = rec.hours_to_work - tolerance_time_of_employee_hours
                difference = rec.work_hours
                if difference > max_tolerance_time_of_compnay:
                    rec.schedule_difference = difference - max_tolerance_time_of_compnay 
                elif difference < max_tolerance_time_of_employee:
                    rec.schedule_difference = difference - max_tolerance_time_of_employee
                else:
                    rec.schedule_difference = 0.0
            else:
                rec.schedule_difference = 0.0

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

        for employee in employees:
            # Get today's attendances
            days = (date_to_tz - date_from_tz).days
            current_date = date_from_tz
            current_date_from = date_from_utc
            for _ in range(0, days+1):
                tomorrow = current_date_from + timedelta(days=1)
                attendances = self.env["hr.attendance"].search([
                    ("employee_id", "=", employee.id),
                    "|",
                    "&",
                    ("check_in", ">=", current_date_from),
                    ("check_in", "<", tomorrow),
                    "&",
                    ("check_out", ">=", current_date_from),
                    ("check_out", "<", tomorrow),
                ])
                daily_report = self.search([("date", "=", current_date), ("employee_id", "=", employee.id)])
                not_working_day_or_leave = self._not_working_day_or_leave(employee, current_date)
                is_not_working_day = not_working_day_or_leave["not_working_day"]
                leave = not_working_day_or_leave["leave"] if not_working_day_or_leave["leave"].holiday_id else False
                weekday = current_date.weekday()
                work_schedules = employee.resource_calendar_id.attendance_ids.filtered(
                lambda x: int(x.dayofweek) == weekday
                )
                # How many hours an employee should work in particular day
                hours_to_work = sum(
                work_schedule.hour_to - work_schedule.hour_from for work_schedule in work_schedules
                )
                if not daily_report:
                    daily_report = self.create({
                        "date": current_date,
                        "employee_id": employee.id,
                        "hours_to_work": hours_to_work,
                        "hour_from": min(work_schedules.mapped("hour_from") or [0]),
                        "hour_to": max(work_schedules.mapped("hour_to") or [0]),
                        "is_not_working_day": is_not_working_day,
                        "holiday_id":  leave.holiday_id.id if leave else False,
                    })

                if attendances:
                    attendance_data = self._get_attendance_data(attendances, current_date)
                    check_in, check_in_location = min(attendance_data, key=lambda x: x[0])
                    check_out, check_out_location = max(attendance_data, key=lambda x: x[0])
                    #if difference is 1 minute check_out shouldn't set
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
                current_date_from += timedelta(days=1)
