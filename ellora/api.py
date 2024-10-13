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
            c.customer_name,
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