import frappe

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
            sii.rate
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