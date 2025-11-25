/** @odoo-module **/

import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class CSMDashboard extends Component {
    setup() {
        this.rpc = useService("rpc");
        this.action = useService("action");
        this.state = useState({
            dashboardData: {},
            loading: true
        });

        onWillStart(async () => {
            await this.loadDashboardData();
        });
    }

    async loadDashboardData() {
        try {
            const data = await this.rpc("/csm/dashboard/data");
            this.state.dashboardData = data;
            this.state.loading = false;
        } catch (error) {
            console.error("Error loading dashboard data:", error);
            this.state.loading = false;
        }
    }

    async onWidgetClick(widgetType) {
        try {
            const result = await this.rpc("/csm/widget/data", {
                widget_type: widgetType
            });
            
            if (result.records && result.records.length > 0) {
                this.action.doAction({
                    type: 'ir.actions.act_window',
                    name: this.getWidgetTitle(widgetType),
                    res_model: result.model,
                    view_mode: 'tree,form',
                    views: [[false, 'list'], [false, 'form']],
                    domain: result.domain,
                    target: 'current',
                });
            }
        } catch (error) {
            console.error("Error loading widget data:", error);
        }
    }

    getWidgetTitle(widgetType) {
        const titles = {
            'red_zone': 'Red Zone Clients',
            'amber_zone': 'Amber Zone Clients', 
            'green_zone': 'Green Zone Clients',
            'total_meetings': 'Total Meetings',
            'task_escalations': 'Task Escalations'
        };
        return titles[widgetType] || 'Records';
    }
}

CSMDashboard.template = "csm_customization.CSMDashboard";

registry.category("actions").add("csm_dashboard", CSMDashboard);
