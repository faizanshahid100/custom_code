from odoo import models, fields, api


class HrOfferSendBackWizard(models.TransientModel):
    _name = "hr.offer.sendback.wizard"
    _description = "Send Back Offer Wizard"

    description = fields.Text("Reason for Sending Back", required=True)

    def action_confirm(self):
        """Apply send back with reason"""
        active_id = self.env.context.get("active_id")
        if active_id:
            offer = self.env["hr.offer"].browse(active_id)
            offer.write({
                "state": "modification",
                'remarks': self.description
            })
            offer.message_post(body=f"<b>Offer Sent Back:</b><br/>{self.description}")
            # Notify submitter by email
            if offer.offer_submitter_id and offer.offer_submitter_id.email:
                mail_template = self.env.ref(
                    "employee_onboarding_offboarding.candidate_offer_modification_template",
                    raise_if_not_found=False
                )
                if mail_template:
                    mail_template.send_mail(offer.id, force_send=True, email_values={
                        "email_to": offer.offer_submitter_id.email,
                    })
        return {"type": "ir.actions.act_window_close"}
