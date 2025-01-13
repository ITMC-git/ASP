from odoo import models
import calendar
from datetime import datetime


class StateReport(models.AbstractModel):
    _name = "report.georgian_worked_hours_report.state_report_xlsx"
    _inherit = "report.report_xlsx.abstract"
    _description = "State Report"

    def generate_xlsx_report(self, workbook, data, employees):
        sheet = workbook.add_worksheet("Report")
        f_1 = workbook.add_format({'bold': True, "align": "center", "border": 1, "valign": "vcenter", "text_wrap": True, })
        generate_date = data["generate_date"]
        date_format = "%Y-%m-%d"
        f_generate_date = datetime.strptime(generate_date, date_format)
        sheet.set_column(0, 0, 44)
        sheet.set_column(1, 1, 15)
        sheet.set_column(2, 2, 35)
        sheet.merge_range(0, 0, 0, 39, "test", f_1)
        sheet.merge_range(1, 0, 1, 39, "სამუშაო დროის აღრიცხვის ფორმა", f_1)
        sheet.merge_range(2, 0, 2, 2, "ორგანიზაციის დასახელება", f_1)
        sheet.merge_range(3, 0, 3, 2, "საიდენტიფიკაციო კოდი", f_1)
        sheet.merge_range(4, 0, 4, 2, "სტრუქტურული ერთეული", f_1)
        sheet.merge_range(5, 0, 5, 2, "შედგენის თარიღი", f_1)
        sheet.merge_range(6, 0, 6, 2, "საანგარიშო პერიოდი", f_1)
        sheet.merge_range(2, 3, 2, 39, "ასპ გრუპი", f_1)
        sheet.merge_range(3, 3, 3, 39, "111test111", f_1)
        sheet.merge_range(4, 3, 4, 39, "ავტოსერვისი ლილო", f_1)
        sheet.merge_range(5, 3, 5, 4, generate_date, f_1)
        sheet.write(6, 3, "-დან", f_1)
        sheet.write(6, 4, "-მდე", f_1)
        sheet.merge_range(5, 5, 6, 39, "Test", f_1)
        sheet.merge_range(7, 0 , 8, 39, None, f_1)
        sheet.merge_range(9, 0, 13, 0, "გვარი, სახელი", f_1)
        sheet.merge_range(9, 1, 13, 1, "პირადი ნომერი/ტაბელის ნომერი", f_1)
        sheet.merge_range(9, 2, 13, 2, "თანამდებობა, (სპეციალობა, პროფესია)", f_1)
        days_in_month = calendar.monthrange(f_generate_date.year, f_generate_date.month)[1]
        sheet.merge_range(9, 3, 9, days_in_month + 2, "აღნიშვნები სამუშაოზე გამოცხადების/არგამოცხადების შესახებ თარიღების მიხედვით თვის განმავლობაში", f_1)
        for day in range(1, days_in_month + 1):
            sheet.merge_range(10, day+2, 13, day+2, day, f_1)
        
        sheet.merge_range(9, days_in_month + 3, 9, 39, "სულ ნამუშევარი თვის განმავლობაში", f_1)
        sheet.merge_range(10, days_in_month + 3, 13, days_in_month + 3, "დღე", f_1)
        sheet.merge_range(10, days_in_month + 4, 10, 39, "საათი", f_1)
        sheet.merge_range(11, days_in_month + 4, 13, days_in_month + 4, "ჯამი", f_1)
        sheet.merge_range(11, days_in_month + 5, 11, 39, "მათ შორის", f_1)
        sheet.merge_range(12, days_in_month + 5, 13, days_in_month + 5, "ზეგანაკვეთური", f_1)
        sheet.merge_range(12, days_in_month + 6, 13, days_in_month + 6, "ღამე", f_1)
        sheet.merge_range(12, days_in_month + 7, 13, days_in_month + 7, "დასვენება/ უქმე დღეებში ნამუშევარი საათების ჯამური რაოდენობა (თვე)", f_1)
        sheet.merge_range(12, days_in_month + 8, 13, 39, "სხვა (საჭიროების შემთხვევაში)", f_1)
        sheet.write(14, 0, "1", f_1)
        sheet.write(14, 1, "2", f_1)
        sheet.write(14, 2, "3", f_1)
        sheet.merge_range(14, 3, 14, days_in_month + 2, "4", f_1)
        sheet.write(14, days_in_month + 3, "5", f_1)
        sheet.write(14, days_in_month + 4, "6", f_1)
        sheet.write(14, days_in_month + 5, "7", f_1)
        sheet.write(14, days_in_month + 6, "8", f_1)
        sheet.write(14, days_in_month + 7, "9", f_1)
        if days_in_month != 31:
            sheet.merge_range(14, days_in_month + 8, 14, 39, "10", f_1)
        else:
            sheet.write(14, 39, "10", f_1)
        employees = self.env["hr.employee"].search([('department_id', '=', data["department_id"])])
        row = 14
        for employee in employees:
            row += 1
            sheet.write(row, 0, employee.name, f_1)
            sheet.write(row, 1, employee.identification_id, f_1)
            sheet.write(row, 2, employee.job_id.name, f_1)
