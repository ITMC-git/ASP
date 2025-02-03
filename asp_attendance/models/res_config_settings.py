import mysql.connector

from odoo import fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    asp_db_user = fields.Char(
        string="Database User",
        help="Database User from ASP mySQL Database.",
        config_parameter="asp.asp_db_user",
        required=True,
    )
    asp_db_password = fields.Char(
        string="Database Password",
        config_parameter="asp.asp_db_password",
        required=True,
    )
    asp_db_name = fields.Char(
        string="Database Name",
        config_parameter="asp.asp_db_name",
        required=True,
    )
    asp_db_host = fields.Char(
        string="Database Host",
        config_parameter="asp.asp_db_host",
        required=True,
    )
    asp_db_port = fields.Char(
        string="Database Port",
        default="3306",
        config_parameter="asp.asp_db_port",
        required=True,
    )
    last_successful_attendance_fetch = fields.Datetime(
        string="Last Successful Attendance Fetch",
        config_parameter="asp.last_successful_attendance_fetch",
    )
    it_support_email = fields.Char(
        string="IT Support Emails",
        required=True,
        config_parameter="asp.it_support_email",
    )

    def check_database_connection(self):
        self.ensure_one()
        try:
            conn = mysql.connector.connect(
                host=self.asp_db_host,
                user=self.asp_db_user,
                password=self.asp_db_password,
                database=self.asp_db_name,
                port=int(self.asp_db_port),
            )
            conn.close()
            notification = {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Success"),
                    "type": "success",
                    "message": "Connection Successful.",
                    "sticky": False,
                }
            }
            return notification
        except mysql.connector.Error as err:
            notification = {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Warning"),
                    "type": "warning",
                    "message": str(err),
                    "sticky": False,
                }
            }
            return notification

    def refetch_attendances(self):
        last_successful_attendance_fetch = self.last_successful_attendance_fetch
        if last_successful_attendance_fetch:
            attendances = self.env["hr.attendance"].search([])
            attendance_to_delete = attendances.filtered(
                lambda x: x.check_in.date() >= last_successful_attendance_fetch.date()
            )
            attendance_to_delete.sudo().unlink()
            updated_attendances = self.env["hr.attendance"].search([])
            checkout_attendance = updated_attendances.filtered(
                lambda x: x.check_out and x.check_out.date() >= last_successful_attendance_fetch.date()
            )
            checkout_attendance.check_out = False
            self.env["hr.attendance"].fetch_asp_attendance()
            self.env["daily.reporting"].create_daily_report(last_successful_attendance_fetch.date(), fields.Date.today())
        return True