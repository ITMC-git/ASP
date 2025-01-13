from odoo import fields, models


class StateReportWizard(models.TransientModel):
    _name = "state.report.wizard"
    _description = "State Report Wizard"

    generate_date = fields.Date(required=True)
    department_id = fields.Many2one("hr.department", required=True)

    def action_generate_report(self):
        data = {
            'generate_date': self.generate_date,
            'department_id': self.department_id.id,
        }
        return self.env.ref('georgian_worked_hours_report.state_report_action').report_action(self, data=data)