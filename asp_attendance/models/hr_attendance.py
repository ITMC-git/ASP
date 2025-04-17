from datetime import datetime

import psycopg2
from odoo import models, fields
import logging

_logger = logging.getLogger(__name__)


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    check_in_location = fields.Char(default="Odoo")
    check_out_location = fields.Char(default="Odoo")
    change_reason = fields.Char()
    
    def get_postgresql_connection(self):
        try:
            # Configure PostgreSQL connection
            config_parameter_model = self.env["ir.config_parameter"].sudo()
            db_config = {
                "user": config_parameter_model.get_param("asp.asp_db_user"),
                "password": config_parameter_model.get_param("asp.asp_db_password"),
                "host": config_parameter_model.get_param("asp.asp_db_host"),
                "dbname": config_parameter_model.get_param("asp.asp_db_name"),
                "port": config_parameter_model.get_param("asp.asp_db_port") or 5432,
            }

            # Connect to PostgreSQL database
            cnx = psycopg2.connect(
                user=db_config["user"],
                password=db_config["password"],
                host=db_config["host"],
                dbname=db_config["dbname"],
                port=db_config["port"],
            )
            return cnx

        except psycopg2.Error as err:
            error_message = f"Failed to connect to the remote PostgreSQL database: {err}"
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
        cnx = self.get_postgresql_connection()
        if cnx is None:
            return

        try:
            with cnx.cursor() as cursor:
                # Fetch last successful fetch time
                config_parameter_model = self.env["ir.config_parameter"].sudo()
                last_fetch_str = config_parameter_model.get_param("asp.last_successful_attendance_fetch") or '1990-01-01 00:00:00'
                last_fetch = fields.Datetime.to_datetime(last_fetch_str)
                # Query attendance records
                query = """
                    SELECT * FROM attendancerecordinfo
                    WHERE AttendanceDateTime >= %s
                    ORDER BY AttendanceDateTime, PersonID;
                """
                cursor.execute(query, (last_fetch,))
                attendance_records = cursor.fetchall()
                # Process attendance records
                attendance_model = self.env['hr.attendance']
                for record in attendance_records:
                    employee_asp_id = record[0]
                    attendance_datetime = record[3]
                    device_name = record[7]
                    employee = self.env["hr.employee"].search([("asp_employee_id", "=", employee_asp_id)], limit=1)
                    if not employee:
                        continue

                    existing_attendance = attendance_model.search([
                        ("employee_id", "=", employee.id),
                        ("check_in", "<=", attendance_datetime),
                    ], order='check_in desc', limit=1)

                    if existing_attendance and not existing_attendance.check_out:
                        if existing_attendance.check_in != attendance_datetime:
                            existing_attendance.check_out = attendance_datetime
                            existing_attendance.check_out_location = device_name
                    elif not existing_attendance or (
                            existing_attendance.check_out != attendance_datetime
                            and existing_attendance.check_in != attendance_datetime
                    ):
                        attendance_model.create({
                            "employee_id": employee.id,
                            "check_in": attendance_datetime,
                            "check_in_location": device_name,
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
