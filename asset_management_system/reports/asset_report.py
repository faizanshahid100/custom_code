from odoo import models, api


class AssetReportPDF(models.AbstractModel):
    _name = 'report.asset_management_system.asset_report_template'
    _description = 'Asset Management Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        assets = self.env['asset.management.asset'].browse(docids)
        
        # Count assets by state
        state_counts = {
            'in_store': 0,
            'in_running': 0,
            'in_repair': 0,
            'scraped': 0
        }
        
        for asset in assets:
            if asset.state in state_counts:
                state_counts[asset.state] += 1
        
        return {
            'doc_ids': docids,
            'doc_model': 'asset.management.asset',
            'docs': assets,
            'state_counts': state_counts,
            'company': self.env.company,
        }
