import frappe

@frappe.whitelist()
def get_stock_info(doctype=None, name=None, item=None, uom=None):
    if item:
        filters = 'a.item_code = %s'
        values = [item]
    elif doctype and name:
        item_list = frappe.get_all(
            doctype= str(doctype) + " Item",
            filters={"parent": name},
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

    if data and uom:
        for item in data:
            if frappe.db.exists("UOM Conversion Detail", {"uom": uom, "parent": item["item_code"]}):
                conversion_factor = frappe.db.get_value("UOM Conversion Detail", {"uom": uom, "parent": item["item_code"]}, "conversion_factor")
                frappe.log_error("conversion_factor", conversion_factor)
                item["stock_uom"] = uom
                item["actual_qty"] = round(item["actual_qty"] / conversion_factor, 2)
                item["reserved_qty"] = round(item["reserved_qty"] / conversion_factor, 2)

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





from erpnext.accounts.doctype.sales_invoice.sales_invoice import get_received_items, validate_inter_company_transaction, get_inter_company_details, \
                                                                    set_purchase_references, update_address, update_taxes
@frappe.whitelist()
def make_and_save_purchase_invoice(source_name):
    purchase_invoice = make_inter_company_purchase_invoice(source_name)
    purchase_invoice.save(ignore_permissions=True)
    return purchase_invoice.name

def make_inter_company_purchase_invoice(source_name, target_doc=None):
    return make_inter_company_transaction("Sales Invoice", source_name, target_doc)

def make_inter_company_transaction(doctype, source_name, target_doc=None):
    if doctype in ["Sales Invoice", "Sales Order"]:
        source_doc = frappe.get_doc(doctype, source_name)
        target_doctype = "Purchase Invoice" if doctype == "Sales Invoice" else "Purchase Order"
        target_detail_field = "sales_invoice_item" if doctype == "Sales Invoice" else "sales_order_item"
        source_document_warehouse_field = "target_warehouse"
        target_document_warehouse_field = "from_warehouse"
        received_items = get_received_items(source_name, target_doctype, target_detail_field)
    else:
        source_doc = frappe.get_doc(doctype, source_name)
        target_doctype = "Sales Invoice" if doctype == "Purchase Invoice" else "Sales Order"
        source_document_warehouse_field = "from_warehouse"
        target_document_warehouse_field = "target_warehouse"
        received_items = {}

    validate_inter_company_transaction(source_doc, doctype)
    details = get_inter_company_details(source_doc, doctype)

    def set_missing_values(source, target):
        target.run_method("set_missing_values")
        set_purchase_references(target)

    def update_details(source_doc, target_doc, source_parent):
        target_doc.inter_company_invoice_reference = source_doc.name
        if target_doc.doctype in ["Purchase Invoice", "Purchase Order"]:
            currency = frappe.db.get_value("Supplier", details.get("party"), "default_currency")
            target_doc.company = details.get("company")
            target_doc.supplier = details.get("party")
            target_doc.is_internal_supplier = 1
            target_doc.ignore_pricing_rule = 1
            target_doc.buying_price_list = source_doc.selling_price_list

            # Invert Addresses
            update_address(target_doc, "supplier_address", "address_display", source_doc.company_address)
            update_address(
                target_doc, "shipping_address", "shipping_address_display", source_doc.customer_address
            )
            update_address(
                target_doc, "billing_address", "billing_address_display", source_doc.customer_address
            )

            if currency:
                target_doc.currency = currency

            update_taxes(
                target_doc,
                party=target_doc.supplier,
                party_type="Supplier",
                company=target_doc.company,
                doctype=target_doc.doctype,
                party_address=target_doc.supplier_address,
                company_address=target_doc.shipping_address,
            )

            if target_doc.doctype == "Purchase Invoice":
                target_doc.set_warehouse = None
                target_doc.set_from_warehouse = None
                target_doc.rejected_warehouse = None
                target_doc.cost_center = None
        else:
            currency = frappe.db.get_value("Customer", details.get("party"), "default_currency")
            target_doc.company = details.get("company")
            target_doc.customer = details.get("party")
            target_doc.selling_price_list = source_doc.buying_price_list

            update_address(
                target_doc, "company_address", "company_address_display", source_doc.supplier_address
            )
            update_address(
                target_doc, "shipping_address_name", "shipping_address", source_doc.shipping_address
            )
            update_address(target_doc, "customer_address", "address_display", source_doc.shipping_address)

            if currency:
                target_doc.currency = currency

            update_taxes(
                target_doc,
                party=target_doc.customer,
                party_type="Customer",
                company=target_doc.company,
                doctype=target_doc.doctype,
                party_address=target_doc.customer_address,
                company_address=target_doc.company_address,
                shipping_address_name=target_doc.shipping_address_name,
            )

    def update_item(source, target, source_parent):
        target.qty = flt(source.qty) - received_items.get(source.name, 0.0)
        if source.doctype == "Purchase Order Item" and target.doctype == "Sales Order Item":
            target.purchase_order = source.parent
            target.purchase_order_item = source.name
            target.material_request = source.material_request
            target.material_request_item = source.material_request_item

        if (
            source.get("purchase_order")
            and source.get("purchase_order_item")
            and target.doctype == "Purchase Invoice Item"
        ):
            target.purchase_order = source.purchase_order
            target.po_detail = source.purchase_order_item

        if target.doctype == "Purchase Invoice Item":
            target.warehouse = None
            target.rejected_warehouse = None

    item_field_map = {
        "doctype": target_doctype + " Item",
        "field_no_map": ["income_account", "expense_account", "cost_center", "warehouse"],
        "field_map": {
            "rate": "rate",
        },
        "postprocess": update_item,
        "condition": lambda doc: doc.qty > 0,
    }

    if doctype in ["Sales Invoice", "Sales Order"]:
        item_field_map["field_map"].update(
            {
                "name": target_detail_field,
            }
        )

    if source_doc.get("update_stock"):
        item_field_map["field_map"].update(
            {
                source_document_warehouse_field: target_document_warehouse_field,
                "batch_no": "batch_no",
                "serial_no": "serial_no",
            }
        )
    elif target_doctype == "Sales Order":
        item_field_map["field_map"].update(
            {
                source_document_warehouse_field: "warehouse",
            }
        )

    doclist = get_mapped_doc(
        doctype,
        source_name,
        {
            doctype: {
                "doctype": target_doctype,
                "postprocess": update_details,
                "set_target_warehouse": "set_from_warehouse",
                "field_no_map": ["taxes_and_charges", "set_warehouse", "shipping_address"],
            },
            doctype + " Item": item_field_map,
        },
        target_doc,
        set_missing_values,
    )

    return doclist





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
            pi.docstatus = 1 AND s.is_internal_supplier = 0{filters}
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





from frappe.model.mapper import get_mapped_doc
from frappe.utils import cstr, flt
from frappe.contacts.doctype.address.address import get_company_address
from frappe.model.utils import get_fetch_values
from erpnext.setup.doctype.item_group.item_group import get_item_group_defaults
from erpnext.stock.doctype.item.item import get_item_defaults
# Make Delivery Note from Quotation
@frappe.whitelist()
def make_delivery_note(source_name, target_doc=None):
    from erpnext.stock.doctype.packed_item.packed_item import make_packing_list

    mapper = {
        "Quotation": {"doctype": "Delivery Note", "validation": {"docstatus": ["=", 1]}},
        "Sales Taxes and Charges": {"doctype": "Sales Taxes and Charges", "add_if_empty": True}
    }

    def set_missing_values(source, target):
        frappe.log_error("smv")
        target.run_method("set_missing_values")
        target.run_method("set_po_nos")
        target.run_method("calculate_taxes_and_totals")
        target.run_method("set_use_serial_batch_fields")

        if source.company_address:
            target.update({"company_address": source.company_address})
        else:
            # set company address
            target.update(get_company_address(target.company))

        if target.company_address:
            target.update(get_fetch_values("Delivery Note", "company_address", target.company_address))

        # if invoked in bulk creation, validations are ignored and thus this method is nerver invoked
        if frappe.flags.bulk_transaction:
            # set target items names to ensure proper linking with packed_items
            target.set_new_name()

        make_packing_list(target)

    def condition(doc):
        # make_mapped_doc sets js `args` into `frappe.flags.args`
        if frappe.flags.args and frappe.flags.args.delivery_dates:
            if cstr(doc.delivery_date) not in frappe.flags.args.delivery_dates:
                return False
        return True

    def update_item(source, target, source_parent):
        target.base_amount = flt(source.qty) * flt(source.base_rate)
        target.amount = flt(source.qty) * flt(source.rate)
        target.qty = flt(source.qty)

        item = get_item_defaults(target.item_code, source_parent.company)
        item_group = get_item_group_defaults(target.item_code, source_parent.company)

        if item:
            target.cost_center = (
                item.get("buying_cost_center")
                or item_group.get("buying_cost_center")
            )

    mapper["Quotation Item"] = {
        "doctype": "Delivery Note Item",
        "field_map": {
            "rate": "rate"
        },
        "condition": condition,
        "postprocess": update_item,
    }

    q = frappe.get_doc("Quotation", source_name)
    target_doc = get_mapped_doc("Quotation", q.name, mapper, target_doc)

    # Should be called after mapping items.
    set_missing_values(q, target_doc)

    return target_doc

# @frappe.whitelist()
# def register_cash_customer():
#     cash_customers = frappe.db.sql("""
#         SELECT DISTINCT TRIM(custom_cash_customer_name) AS custom_cash_customer_name
#         FROM `tabSales Invoice`
#         WHERE custom_cash_customer_name IS NOT NULL
#     """, as_dict=True)

#     for customer in cash_customers:
#         if customer.custom_cash_customer_name and not frappe.db.exists("Cash Customer", customer.custom_cash_customer_name):
#             cash_customer = frappe.get_doc({
#                 "doctype": "Cash Customer",
#                 "full_name": customer.custom_cash_customer_name
#             })
#             cash_customer.insert(ignore_permissions=True)
#     frappe.db.commit()

