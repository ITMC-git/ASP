from odoo import fields, models


class StateReportWizard(models.TransientModel):
    _name = "state.report.wizard"
    _description = "State Report Wizard"

    date_of_compilation = fields.Date(required=True)
    generate_date = fields.Date(required=True)
    department_id = fields.Many2one(
        comodel_name="hr.department",
        required=True,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        default=lambda x: x.env.company.id,
    )

    def action_generate_report(self):
        data = {
            "date_of_compilation": self.date_of_compilation,
            "generate_date": self.generate_date,
            "department_id": self.department_id.id,
            "company_id": self.company_id.id
        }
        return self.env.ref("georgian_worked_hours_report.state_report_xlsx").report_action(self, data=data)
