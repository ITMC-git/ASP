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
