
from odoo import models


class StateReport(models.AbstractModel):
    _name = 'report.georgian_worked_hours_report.state_report'
    _description = 'State Report'

    def generate_xlsx_report(self, workbook, data):
        sheet = workbook.add_worksheet('State Report')
        print("generated xlsx report")
        print("Data", data)

       


    