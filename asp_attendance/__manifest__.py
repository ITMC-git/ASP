{
    "name": "ASP Attendance",
    "version": "1.0",
    "description": "ASP Attendance Integration. Fetch data from ASP database.",
    "summary": "ASP Integration",
    "author": "ITMC",
    "license": "LGPL-3",
    "depends": ["hr_attendance"],
    "external_dependencies": {"python": ["mysql-connector-python"]},
    "data": [
        "views/hr_employee_views.xml",
        "views/res_config_settings_views.xml",
    ],

    "application": True,
}
