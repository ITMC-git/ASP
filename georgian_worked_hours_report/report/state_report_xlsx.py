from odoo import models
import calendar
from datetime import datetime


class StateReport(models.AbstractModel):
    _name = "report.georgian_worked_hours_report.state_report_xlsx"
    _inherit = "report.report_xlsx.abstract"
    _description = "State Report"


    def generate_xlsx_report(self, workbook, data, employees):
        # HEADER: Add header related values.
        sheet = workbook.add_worksheet("Report")
        f_1 = workbook.add_format({'bold': True, "align": "center", "border": 1, "valign": "vcenter", "text_wrap": True, })
        company_id = data["company_id"]
        company = self.env["res.company"].browse(company_id)
        date_of_compilation = data["date_of_compilation"]
        generate_date = data["generate_date"]
        date_format = "%Y-%m-%d"
        f_generate_date = datetime.strptime(generate_date, date_format)
        department_id = data["department_id"]
        department = self.env["hr.department"].browse(department_id)

        # Set column widths for better readability
        sheet.set_column(0, 0, 44)
        sheet.set_column(1, 1, 15)
        sheet.set_column(2, 2, 35)

        # Merge header rows to create the report title and company info.
        sheet.merge_range(0, 0, 0, 39, "დანართი N2", f_1)
        sheet.merge_range(1, 0, 1, 39, "სამუშაო დროის აღრიცხვის ფორმა", f_1)
        sheet.merge_range(2, 0, 2, 2, "ორგანიზაციის დასახელება", f_1)
        sheet.merge_range(3, 0, 3, 2, "საიდენტიფიკაციო კოდი", f_1)
        sheet.merge_range(4, 0, 4, 2, "სტრუქტურული ერთეული", f_1)
        sheet.merge_range(5, 0, 5, 2, "შედგენის თარიღი", f_1)
        sheet.merge_range(6, 0, 6, 2, "საანგარიშო პერიოდი", f_1)
        sheet.merge_range(2, 3, 2, 39, company.name, f_1)
        sheet.merge_range(3, 3, 3, 39, company.vat, f_1)
        sheet.merge_range(4, 3, 4, 39, department.name, f_1)
        sheet.merge_range(5, 3, 5, 4, date_of_compilation, f_1)

        # Date range for the report period.
        sheet.write(6, 3, "-დან", f_1)
        sheet.write(6, 4, "-მდე", f_1)
        # Empty row for spacing
        sheet.merge_range(7, 0, 8, 39, None, f_1)
        # HEADER: Define the column titles for employee info and daily work report.
        sheet.merge_range(9, 0, 13, 0, "გვარი, სახელი", f_1)
        sheet.merge_range(9, 1, 13, 1, "პირადი ნომერი/ტაბელის ნომერი", f_1)
        sheet.merge_range(9, 2, 13, 2, "თანამდებობა, (სპეციალობა, პროფესია)", f_1)
    
        # Calculate the number of days in the selected month.
        days_in_month = calendar.monthrange(f_generate_date.year, f_generate_date.month)[1]
        sheet.merge_range(9, 3, 9, days_in_month + 2, "აღნიშვნები სამუშაოზე გამოცხადების/არგამოცხადების შესახებ თარიღების მიხედვით თვის განმავლობაში", f_1)
        first_generate_date = f_generate_date.replace(day=1)
        last_generate_date = f_generate_date.replace(day=days_in_month)
        sheet.merge_range(5, 5, 6, 39, f"{first_generate_date.date()} - {last_generate_date.date()}", f_1)

        # Add day columns for the report.
        for day in range(1, days_in_month + 1):
            sheet.merge_range(10, day+2, 13, day+2, day, f_1)

        # Add summary columns for total worked hours and overtime.
        sheet.merge_range(9, days_in_month + 3, 9, 39, "სულ ნამუშევარი თვის განმავლობაში", f_1)
        sheet.merge_range(10, days_in_month + 3, 13, days_in_month + 3, "დღე", f_1)
        sheet.merge_range(10, days_in_month + 4, 10, 39, "საათი", f_1)
        sheet.merge_range(11, days_in_month + 4, 13, days_in_month + 4, "ჯამი", f_1)
        sheet.merge_range(11, days_in_month + 5, 11, 39, "მათ შორის", f_1)
        sheet.merge_range(12, days_in_month + 5, 13, days_in_month + 5, "ზეგანაკვეთური", f_1)
        sheet.merge_range(12, days_in_month + 6, 13, days_in_month + 6, "ღამე", f_1)
        sheet.merge_range(12, days_in_month + 7, 13, days_in_month + 7, "დასვენება/ უქმე დღეებში ნამუშევარი საათების ჯამური რაოდენობა (თვე)", f_1)
        sheet.merge_range(12, days_in_month + 8, 13, 39, "სხვა (საჭიროების შემთხვევაში)", f_1)
        # Write row labels
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
        # BODY: Add employee-specific data (working hours, overtime, etc.)
        employees = self.env["hr.employee"].search([('department_id', '=', department_id)])
        row = 14
        last_column =  self.get_column_letter(days_in_month)
        for employee in employees:
            row += 1
            sheet.write(row, 0, employee.name, f_1)
            sheet.write(row, 1, employee.identification_id, f_1)
            sheet.write(row, 2, employee.job_id.name, f_1)
            # Fetch daily reports for the employee within the report period.
            first_day = f_generate_date.replace(day=1)
            last_day = f_generate_date.replace(day=days_in_month)
            daily_reports = self.env["daily.reporting"].search([
                ("employee_id", "=", employee.id),
                ("date", ">=", first_day),
                ("date", "<=", last_day)
            ])
            # Write data for each day of the month.
            for day in range(1, days_in_month + 1):
                current_date = f_generate_date.replace(day=day)
                daily_report = daily_reports.filtered(lambda x: x.date == current_date.date())
                if daily_report:
                    if daily_report.is_not_working_day:
                        sheet.write(row, day + 2, "დ", f_1)
                    elif daily_report.work_hours == 0.0:
                        sheet.write(row, day + 2, "გ", f_1)
                    else:
                        sheet.write(row, day + 2, round(daily_report.work_hours, 2), f_1)
                else:
                    sheet.write(row, day + 2, None, f_1)
                # Placeholder for total worked hours and overtime.
                sheet.write_formula(row, days_in_month + 3, f"=COUNT(D{row+1}:{last_column}{row+1})", f_1)
                sheet.write_formula(row, days_in_month + 4, f"=SUM(D{row+1}:{last_column}{row+1})", f_1)
                sheet.write(row, days_in_month + 5, None, f_1)
                sheet.write(row, days_in_month + 6, None, f_1)
                sheet.write(row, days_in_month + 7, None, f_1)
                if days_in_month != 31:
                    sheet.merge_range(row, days_in_month + 8, row, 39, None, f_1)
                else:
                    sheet.write(row, 39, None, f_1)
        # FOOTER: Add footer and signature fields.
        sheet.merge_range(row + 3, 0, row + 4, 2, "ორგანიზაციის/სტრუქტურული ქვედანაყოფის ხელმძღვანელი", f_1)
        sheet.merge_range(row + 3, 3, row + 3, 7, None, f_1)
        sheet.merge_range(row + 4, 3, row + 4, 7, "გვარი, სახელი", f_1)
        sheet.merge_range(row + 3, 10, row + 3, 11, None, f_1)
        sheet.merge_range(row + 4, 10, row + 4, 11, "ხელმოწერა", f_1)

        sheet.merge_range(row + 6, 0, row + 7, 2, "ტაბელის შედგენაზე პასუხისმგებელი პირი", f_1)
        sheet.merge_range(row + 6, 3, row + 6, 7, None, f_1)
        sheet.merge_range(row + 7, 3, row + 7, 7, "გვარი, სახელი", f_1)
        sheet.merge_range(row + 6, 10, row + 6, 11, None, f_1)
        sheet.merge_range(row + 7, 10, row + 7, 11, "ხელმოწერა", f_1)

    def get_column_letter(self, days_in_month):
        base_col = 68
        column_index = base_col + days_in_month - 1

        if column_index <= 90:
            return chr(column_index)
        else:
            first_letter = chr((column_index - 65) // 26 + 64)
            second_letter = chr((column_index - 65) % 26 + 65)
            return first_letter + second_letter