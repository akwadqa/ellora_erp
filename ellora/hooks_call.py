import frappe
from frappe import _


def validate_minimum_selling_rate(doc, method):
    if doc.doctype == "Sales Invoice":
        if doc.is_internal_customer:
            return
        
    if doc.items:
        for item in doc.items:
            if item.rate:
                minimum_selling_rate = frappe.db.get_value("Item", item.item_code, "custom_minimum_selling_rate")
                if minimum_selling_rate and minimum_selling_rate > 0:
                    if item.rate < minimum_selling_rate:
                        frappe.throw(_("Minimum selling rate exceeded for {0}: {1}").format(item.item_code, _(item.item_name)))





def clear_warehouse_fields(doc, method):
    if doc.doctype == "Purchase Receipt":
        for item in doc.items:
            item.rejected_warehouse = None





def uncheck_update_stock(doc, method):
    if doc.items:
        if doc.items[0].delivery_note:
            if doc.update_stock == 1:
                doc.update_stock = 0