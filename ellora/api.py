import frappe
from erpnext.accounts.doctype.sales_invoice.sales_invoice import make_inter_company_purchase_invoice

@frappe.whitelist()
def get_stock_info(sales_invoice=None, item=None):
    if item:
        filters = 'a.item_code = %s'
        values = [item]
    elif sales_invoice:
        item_list = frappe.get_all(
            doctype="Sales Invoice Item",
            filters={"parent": sales_invoice},
            fields=["item_code"]
        )
        if not item_list:
            return []
        
        placeholders = ', '.join(['%s'] * len(item_list))
        filters = f'a.item_code IN ({placeholders})'
        values = [d['item_code'] for d in item_list]
    else:
        return []
    
    query = f"""
        SELECT 
            a.item_code, a.item_name, a.stock_uom, b.warehouse, b.actual_qty, b.reserved_qty
        FROM 
            `tabItem` a
        LEFT JOIN 
            `tabBin` b ON a.item_code = b.item_code
        WHERE 
            {filters}
    """
    data = frappe.db.sql(query, values, as_dict=True)

    return data


@frappe.whitelist()
def get_item_sales_history(customer=None, item=None):
    filters = []
    values = []

    if customer:
        filters.append('si.customer = %s')
        values.append(customer)

    if item:
        filters.append('sii.item_code = %s')
        values.append(item)

    if filters:
        filters = ' AND ' + ' AND '.join(filters)
    else:
        filters = ""

    query = f"""
        SELECT
            CASE
                WHEN si.customer = 'Cash Customer' THEN si.custom_cash_customer_name
                ELSE c.customer_name
            END AS customer_name,
            si.name as sales_invoice,
            si.posting_date,
            sii.item_code,
            sii.item_name,
            sii.qty,
            sii.rate,
            sii.uom
        FROM
            `tabSales Invoice` si
        JOIN
            `tabSales Invoice Item` sii ON si.name = sii.parent
        JOIN
            `tabCustomer` c ON si.customer = c.name
        WHERE
            si.docstatus = 1{filters}
        ORDER BY
            si.posting_date DESC
    """
    item_sales_history = frappe.db.sql(query, tuple(values), as_dict=True)

    if not item_sales_history:
        return []
    
    return item_sales_history





# Valuation Rate
@frappe.whitelist()
def get_valuation_rate(item_code, warehouse):
    valuation_rate = frappe.get_value("Bin", {"item_code": item_code, "warehouse": warehouse}, "valuation_rate")
    return valuation_rate if valuation_rate else 0





@frappe.whitelist()
def make_and_save_purchase_invoice(source_name):
    purchase_invoice = make_inter_company_purchase_invoice(source_name)
    purchase_invoice.save(ignore_permissions=True)
    return purchase_invoice.name





@frappe.whitelist()
def get_quotation_item_sales_history(customer=None, item=None):
    filters = []
    values = []

    if customer:
        filters.append('q.party_name = %s')
        values.append(customer)

    if item:
        filters.append('qi.item_code = %s')
        values.append(item)

    if filters:
        filters = ' AND ' + ' AND '.join(filters)
    else:
        filters = ""

    query = f"""
        SELECT
            c.customer_name,
            q.name as quotation,
            q.transaction_date,
            qi.item_code,
            qi.item_name,
            qi.qty,
            qi.rate,
            qi.uom
        FROM
            `tabQuotation` q
        JOIN
            `tabQuotation Item` qi ON q.name = qi.parent
        JOIN
            `tabCustomer` c ON q.party_name = c.name
        WHERE
            q.docstatus = 1{filters}
        ORDER BY
            q.transaction_date DESC
    """
    quotation_item_sales_history = frappe.db.sql(query, tuple(values), as_dict=True)

    if not quotation_item_sales_history:
        return []
    
    return quotation_item_sales_history





@frappe.whitelist()
def get_delivery_note_item_sales_history(customer=None, item=None):
    filters = []
    values = []

    if customer:
        filters.append('dn.customer = %s')
        values.append(customer)

    if item:
        filters.append('dni.item_code = %s')
        values.append(item)

    if filters:
        filters = ' AND ' + ' AND '.join(filters)
    else:
        filters = ""

    query = f"""
        SELECT
            c.customer_name,
            dn.name as delivery_note,
            dn.posting_date,
            dni.item_code,
            dni.item_name,
            dni.qty,
            dni.rate,
            dni.uom
        FROM
            `tabDelivery Note` dn
        JOIN
            `tabDelivery Note Item` dni ON dn.name = dni.parent
        JOIN
            `tabCustomer` c ON dn.customer = c.name
        WHERE
            dn.docstatus = 1{filters}
        ORDER BY
            dn.posting_date DESC
    """
    delivery_note_item_sales_history = frappe.db.sql(query, tuple(values), as_dict=True)

    if not delivery_note_item_sales_history:
        return []
    
    return delivery_note_item_sales_history





@frappe.whitelist()
def get_purchase_order_item_sales_history(supplier=None, item=None):
    filters = []
    values = []

    if supplier:
        filters.append('po.supplier = %s')
        values.append(supplier)

    if item:
        filters.append('poi.item_code = %s')
        values.append(item)

    if filters:
        filters = ' AND ' + ' AND '.join(filters)
    else:
        filters = ""

    query = f"""
        SELECT
            s.supplier_name,
            po.name as purchase_order,
            po.transaction_date,
            poi.item_code,
            poi.item_name,
            poi.qty,
            poi.rate,
            poi.uom
        FROM
            `tabPurchase Order` po
        JOIN
            `tabPurchase Order Item` poi ON po.name = poi.parent
        JOIN
            `tabSupplier` s ON po.supplier = s.name
        WHERE
            po.docstatus = 1{filters}
        ORDER BY
            po.transaction_date DESC
    """
    purchase_order_item_sales_history = frappe.db.sql(query, tuple(values), as_dict=True)

    if not purchase_order_item_sales_history:
        return []
    
    return purchase_order_item_sales_history





@frappe.whitelist()
def get_purchase_invoice_item_sales_history(supplier=None, item=None):
    filters = []
    values = []

    if supplier:
        filters.append('pi.supplier = %s')
        values.append(supplier)

    if item:
        filters.append('pii.item_code = %s')
        values.append(item)

    if filters:
        filters = ' AND ' + ' AND '.join(filters)
    else:
        filters = ""

    query = f"""
        SELECT
            s.supplier_name,
            pi.name as purchase_invoice,
            pi.posting_date,
            pii.item_code,
            pii.item_name,
            pii.qty,
            pii.rate,
            pii.uom
        FROM
            `tabPurchase Invoice` pi
        JOIN
            `tabPurchase Invoice Item` pii ON pi.name = pii.parent
        JOIN
            `tabSupplier` s ON pi.supplier = s.name
        WHERE
            pi.docstatus = 1{filters}
        ORDER BY
            pi.posting_date DESC
    """
    purchase_invoice_item_sales_history = frappe.db.sql(query, tuple(values), as_dict=True)

    if not purchase_invoice_item_sales_history:
        return []
    
    return purchase_invoice_item_sales_history





@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_item_uoms(doctype, txt, searchfield, start, page_len, filters):
    """
    Fetch UOMs from the UOM Conversion Detail child table of the Item doctype.
    """

    # filters = frappe.parse_json(filters) # Convert filters from JSON string to dict
    item_code = filters.get("value")

    if not item_code:
        return []

    return frappe.get_all(
        "UOM Conversion Detail",
        filters={"parent": item_code},
        fields=["uom"],
        as_list=1,
    )





# from frappe.model.mapper import get_mapped_doc
# from frappe.utils import cstr, flt
# from frappe.contacts.doctype.address.address import get_company_address
# from frappe.model.utils import get_fetch_values
# from erpnext.setup.doctype.item_group.item_group import get_item_group_defaults
# from erpnext.stock.doctype.item.item import get_item_defaults
# # Make Delivery Note from Quotation
# @frappe.whitelist()
# def make_delivery_note(source_name, target_doc=None, kwargs=None):
# 	from erpnext.stock.doctype.packed_item.packed_item import make_packing_list
# 	from erpnext.stock.doctype.stock_reservation_entry.stock_reservation_entry import (
# 		get_sre_details_for_voucher,
# 		get_sre_reserved_qty_details_for_voucher,
# 		get_ssb_bundle_for_voucher,
# 	)

# 	if not kwargs:
# 		kwargs = {
# 			"for_reserved_stock": frappe.flags.args and frappe.flags.args.for_reserved_stock,
# 			"skip_item_mapping": frappe.flags.args and frappe.flags.args.skip_item_mapping,
# 		}

# 	kwargs = frappe._dict(kwargs)

# 	sre_details = {}
# 	if kwargs.for_reserved_stock:
# 		sre_details = get_sre_reserved_qty_details_for_voucher("Quotation", source_name)

# 	mapper = {
# 		"Quotation": {"doctype": "Delivery Note", "validation": {"docstatus": ["=", 1]}},
# 		"Sales Taxes and Charges": {"doctype": "Sales Taxes and Charges", "add_if_empty": True},
# 		"Sales Team": {"doctype": "Sales Team", "add_if_empty": True},
# 	}

# 	def set_missing_values(source, target):
# 		if kwargs.get("ignore_pricing_rule"):
# 			# Skip pricing rule when the dn is creating from the pick list
# 			target.ignore_pricing_rule = 1

# 		target.run_method("set_missing_values")
# 		target.run_method("set_po_nos")
# 		target.run_method("calculate_taxes_and_totals")
# 		target.run_method("set_use_serial_batch_fields")

# 		if source.company_address:
# 			target.update({"company_address": source.company_address})
# 		else:
# 			# set company address
# 			target.update(get_company_address(target.company))

# 		if target.company_address:
# 			target.update(get_fetch_values("Delivery Note", "company_address", target.company_address))

# 		# if invoked in bulk creation, validations are ignored and thus this method is nerver invoked
# 		if frappe.flags.bulk_transaction:
# 			# set target items names to ensure proper linking with packed_items
# 			target.set_new_name()

# 		make_packing_list(target)

# 	def condition(doc):
# 		if doc.name in sre_details:
# 			del sre_details[doc.name]
# 			return False

# 		# make_mapped_doc sets js `args` into `frappe.flags.args`
# 		if frappe.flags.args and frappe.flags.args.delivery_dates:
# 			if cstr(doc.delivery_date) not in frappe.flags.args.delivery_dates:
# 				return False

# 		return abs(doc.delivered_qty) < abs(doc.qty) and doc.delivered_by_supplier != 1

# 	def update_item(source, target, source_parent):
# 		target.base_amount = (flt(source.qty) - flt(source.delivered_qty)) * flt(source.base_rate)
# 		target.amount = (flt(source.qty) - flt(source.delivered_qty)) * flt(source.rate)
# 		target.qty = flt(source.qty) - flt(source.delivered_qty)

# 		item = get_item_defaults(target.item_code, source_parent.company)
# 		item_group = get_item_group_defaults(target.item_code, source_parent.company)

# 		if item:
# 			target.cost_center = (
# 				frappe.db.get_value("Project", source_parent.project, "cost_center")
# 				or item.get("buying_cost_center")
# 				or item_group.get("buying_cost_center")
# 			)

# 	if not kwargs.skip_item_mapping:
# 		mapper["Quotation Item"] = {
# 			"doctype": "Delivery Note Item",
# 			"field_map": {
# 				"rate": "rate",
# 				"name": "so_detail",
# 				"parent": "against_sales_order",
# 			},
# 			"condition": condition,
# 			"postprocess": update_item,
# 		}

# 	quotation = frappe.get_doc("Quotation", source_name)
# 	target_doc = get_mapped_doc("Quotation", quotation.name, mapper, target_doc)

# 	if not kwargs.skip_item_mapping and kwargs.for_reserved_stock:
# 		sre_list = get_sre_details_for_voucher("Quotation", source_name)

# 		if sre_list:

# 			def update_dn_item(source, target, source_parent):
# 				update_item(source, target, quotation)

# 			quotation_items = {d.name: d for d in quotation.items if d.stock_reserved_qty}

# 			for sre in sre_list:
# 				if not condition(quotation_items[sre.voucher_detail_no]):
# 					continue

# 				dn_item = get_mapped_doc(
# 					"Quotation Item",
# 					sre.voucher_detail_no,
# 					{
# 						"Quotation Item": {
# 							"doctype": "Delivery Note Item",
# 							"field_map": {
# 								"rate": "rate",
# 								"name": "so_detail",
# 								"parent": "against_sales_order",
# 							},
# 							"postprocess": update_dn_item,
# 						}
# 					},
# 					ignore_permissions=True,
# 				)

# 				dn_item.qty = flt(sre.reserved_qty) * flt(dn_item.get("conversion_factor", 1))

# 				if sre.reservation_based_on == "Serial and Batch" and (sre.has_serial_no or sre.has_batch_no):
# 					dn_item.serial_and_batch_bundle = get_ssb_bundle_for_voucher(sre)

# 				target_doc.append("items", dn_item)
# 			else:
# 				# Correct rows index.
# 				for idx, item in enumerate(target_doc.items):
# 					item.idx = idx + 1

# 	# Should be called after mapping items.
# 	set_missing_values(quotation, target_doc)

# 	return target_doc