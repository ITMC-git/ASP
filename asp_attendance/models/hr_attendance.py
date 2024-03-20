import mysql.connector
from odoo import models, fields
import logging

_logger = logging.getLogger(__name__)


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

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
            _logger.error("Failed to connect to the remote MySQL database: %s", err)
            return None

        except Exception as e:
            _logger.error("An error occurred while connecting to the database: %s", e)
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
                    WHERE AttendanceDateTime >= %s;
                """
                cursor.execute(query, (timestamp,))

                # Fetch the attendance records
                attendance_records = cursor.fetchall()

                # Create attendance records in Odoo
                attendance_model = self.env['hr.attendance']
                for record in attendance_records:
                    # Process attendance records and create attendance in Odoo
                    pass
                config_parameter_model.set_param(
                    "asp.last_successful_attendance_fetch",
                    fields.Datetime.to_string(fields.Datetime.now())
                )

        except Exception as e:
            _logger.error("An error occurred while fetching attendance data: %s", e)

        finally:
            cnx.close()
