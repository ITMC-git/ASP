/** @odoo-module */

import { listView } from "@web/views/list/list_view";
import { registry } from "@web/core/registry";
import { DailyReportListController } from './daily_report_list_controller';

export const UpdateDailyReportButtonView = {
    ...listView,
    Controller: DailyReportListController,
    buttonTemplate: 'DailyReport.Buttons',
};

registry.category("views").add("asp_daily_report", UpdateDailyReportButtonView);
