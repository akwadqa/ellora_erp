import frappe
from frappe import _


def validate_minimum_selling_rate(doc, method):
    if doc.items:
        for item in doc.items:
            if item.rate < frappe.db.get_value("Item", item.item_code, "custom_minimum_selling_rate"):
                frappe.throw(_("Minimum selling rate exceeded for {0}: {1}").format(item.item_code, _(item.item_name)))





def clear_warehouse_fields(doc, method):
    if doc.doctype == "Purchase Receipt":
        for item in doc.items:
            item.rejected_warehouse = None