from datetime import datetime

import mysql.connector
from odoo import api, models, fields
import logging

_logger = logging.getLogger(__name__)


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    check_in_location = fields.Char(default="Odoo")
    check_out_location = fields.Char(default="Odoo")
    change_reason = fields.Char()
    
    def get_mysql_connection(self):
        try:
            # Configure MySQL connection
            config_parameter_model = self.env["ir.config_parameter"].sudo()
            db_config = {
                "user": config_parameter_model.get_param("asp.asp_db_user"),
                "password": config_parameter_model.get_param("asp.asp_db_password"),
                "host": config_parameter_model.get_param("asp.asp_db_host"),
                "database": config_parameter_model.get_param("asp.asp_db_name"),
                "port": config_parameter_model.get_param("asp.asp_db_port"),
            }

            # Connect to MySQL database
            cnx = mysql.connector.connect(**db_config)
            return cnx

        except mysql.connector.Error as err:
            error_message = f"Failed to connect to the remote MySQL database: {err}"
            _logger.error(error_message)
            return None

        except Exception as e:
            error_message = f"An error occurred while connecting to the database: {e}"
            _logger.error(error_message)
            return None

    def send_error_email(self, error_message):
        config_parameter_model = self.env["ir.config_parameter"].sudo()
        mail_to = config_parameter_model.get_param("asp.it_support_email")
        if mail_to:
            subject = "ASP Camera Integration Error"
            body = f"Error: {error_message}"
            mail_values = {
                'subject': subject,
                'body_html': body,
                'email_to': mail_to,
            }
            mail_id = self.env['mail.mail'].sudo().create(mail_values)
            mail_id.sudo().send()
        else:
            return None

    def fetch_asp_attendance(self):
        cnx = self.get_mysql_connection()
        if cnx is None:
            return

        try:
            with cnx.cursor() as cursor:
                # Query to fetch attendance data from remote MySQL database
                config_parameter_model = self.env["ir.config_parameter"].sudo()
                last_successful_attendance_fetch = config_parameter_model.get_param(
                    "asp.last_successful_attendance_fetch"
                ) or '1990-01-01 00:00:00'
                last_successful_attendance_fetch = fields.Datetime.to_datetime(last_successful_attendance_fetch)
                timestamp = last_successful_attendance_fetch.timestamp() * 1000
                query = """
                    SELECT * FROM attendancerecordinfo
                    WHERE AttendanceDateTime >= %s
                    ORDER BY AttendanceDateTime, PersonID;
                """
                cursor.execute(query, (timestamp,))

                # Fetch the attendance records
                attendance_records = cursor.fetchall()

                # Create attendance records in Odoo
                attendance_model = self.env['hr.attendance']
                for record in attendance_records:
                    # Process attendance records and create attendance in Odoo
                    employee_id = self.env["hr.employee"].search([("asp_employee_id", "=", record[0])])
                    if not employee_id:
                        continue
                    attendance_date = datetime.fromtimestamp(record[3] / 1000)
                    attendance_location = record[7]  # DeviceName column in attendance record
                    existing_attendance = attendance_model.search([
                        ("employee_id", "=", employee_id.id),
                        ("check_in", "<=", attendance_date),
                    ], order='check_in desc', limit=1)
                    # Update the existing attendance record if it doesn't have a check_out time
                    if existing_attendance and not existing_attendance.check_out:
                        if existing_attendance.check_in != attendance_date:
                            existing_attendance.check_out = attendance_date
                            existing_attendance.check_out_location = attendance_location

                    # Create a new attendance record if:
                    # 1. No existing attendance record is found, or
                    # 2. An existing attendance record is found, but both check_in and check_out times
                    #    are different from the current attendance_date
                    elif not existing_attendance or (
                            existing_attendance
                            and existing_attendance.check_out != attendance_date
                            and existing_attendance.check_in != attendance_date
                    ):
                        attendance_model.create({
                            "employee_id": employee_id.id,
                            "check_in": attendance_date,
                            "check_in_location": attendance_location,
                        })
                if attendance_records:
                    config_parameter_model.set_param(
                        "asp.last_successful_attendance_fetch",
                        fields.Datetime.to_string(fields.Datetime.now())
                    )

        except Exception as e:
            error_message = f"An error occurred while fetching attendance data: {e}"
            _logger.error(error_message)
            self.send_error_email(error_message)

        finally:
            cnx.close()

    @api.depends('check_in', 'check_out')
    def _compute_worked_hours(self):
        """
        COMPLETELY_OVERRIDDEN_METHOD
        """
        for attendance in self:
            if attendance.check_out and attendance.check_in:
                # ASP changes: start
                delta = attendance.check_out - attendance.check_in
                worked_hours = delta.total_seconds() / 3600.0
                # Deduct 1 hour for a break
                if worked_hours > 0:
                    worked_hours -= 1
                # Cap worked hours to 8
                if worked_hours > 8:
                    worked_hours = 8
                attendance.worked_hours = worked_hours
                # ASP changes: end
            else:
                attendance.worked_hours = False
