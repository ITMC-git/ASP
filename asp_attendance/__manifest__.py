{
    "name": "ASP Attendance",
    "version": "1.0",
    "description": "ASP Attendance Integration. Fetch data from ASP database.",
    "summary": "ASP Integration",
    "author": "ITMC",
    "license": "LGPL-3",
    "depends": ["hr_attendance", "hr_holidays", "resource"],
    "external_dependencies": {"python": ["mysql-connector-python"]},
    "data": [
        "security/ir.model.access.csv",
        "data/ir_cron_data.xml",
        "views/hr_employee_views.xml",
        "views/res_config_settings_views.xml",
        "views/daily_reporting_views.xml",
        "views/hr_attendance_views.xml",
    ],

    "application": True,
}
