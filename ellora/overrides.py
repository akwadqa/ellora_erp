import frappe
from frappe import _, msgprint
from frappe.utils import getdate


@frappe.whitelist()
def custom_update_clearance_date(self):
    frappe.log_error("custom_update_clearance_date")
    clearance_date_updated = False
    for d in self.get("payment_entries"):
        if d.clearance_date:
            if not d.payment_document:
                frappe.throw(_("Row #{0}: Payment document is required to complete the transaction"))

            if d.cheque_date and getdate(d.clearance_date) < getdate(d.cheque_date):
                frappe.throw(
                    _("Row #{0}: Clearance date {1} cannot be before Cheque Date {2}").format(
                        d.idx, d.clearance_date, d.cheque_date
                    )
                )

        if d.clearance_date or self.include_reconciled_entries:
            if not d.clearance_date:
                d.clearance_date = None

            payment_entry = frappe.get_doc(d.payment_document, d.payment_entry)
            payment_entry.db_set("clearance_date", d.clearance_date)
            payment_entry.db_set("custom_cheque_status", "Cleared")

            clearance_date_updated = True

    if clearance_date_updated:
        self.get_payment_entries()
        msgprint(_("Clearance Date updated"))
    else:
        msgprint(_("Clearance Date not mentioned"))
