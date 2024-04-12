/** @odoo-module */

import { ListController } from "@web/views/list/list_controller";

export class DailyReportListController extends ListController {
	async actionUpdateDailyReport() {
		return this.actionService.doAction("asp_attendance.update_daily_report_action", {
            additionalContext: {},
            onClose: () => {
                this.model.load();
            },
        });
	}

}
