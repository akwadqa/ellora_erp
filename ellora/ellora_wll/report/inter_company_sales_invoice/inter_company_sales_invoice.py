# Copyright (c) 2025, Akwad Programming and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
    filters = frappe._dict(filters or {})
    columns = get_columns(filters)
    data = get_data(filters)
    return columns, data

def get_columns(filters):
    columns = [
        {
            "label": _("Posting Date"),
            "fieldtype": "Date",
            "fieldname": "si_posting_date",
            "width": 125,
        },
        {
            "label": _("Customer"),
            "fieldtype": "Link",
            "fieldname": "customer_name",
            "options": "User",
            "width": 125,
        },
        {
            "label": _("Sales Invoice"),
            "fieldtype": "Link",
            "fieldname": "sales_invoice",
            "options": "Sales Invoice",
            "width": 200,
        },
         {
            "label": _("Purchase Invoice Status"),
            "fieldtype": "Data",
            "fieldname": "status",
            "width": 100,
        },
        {
            "label": _("Supplier"),
            "fieldtype": "Link",
            "fieldname": "supplier",
            "options": "Supplier",
            "width": 125,
        },
        {
            "label": _("Purchase Invoice Number"),
            "fieldtype": "Link",
            "fieldname": "purchase_invoice_number",
            "options": "Purchase Invoice",
            "width": 250,
        },
        {
            "label": _("Connection"),
            "fieldtype": "Data",
            "fieldname": "connection",
            "width": 75,
        },
        {
            "label": _("Sales Grand total"),
            "fieldtype": "Currency",
            "fieldname": "sales_grand_total",
            "width": 100,
        },
        {
            "label": _("Purchase Grand total"),
            "fieldtype": "Currency",
            "fieldname": "purchase_grand_total",
            "width": 100,
        },
        {
            "label": _("Sales Submission User"),
            "fieldtype": "Data",
            "fieldname": "si_modified_by",
            "width": 200,
        },
        {
            "label": _("Purchase Submission User"),
            "fieldtype": "Data",
            "fieldname": "pi_modified_by",
            "width": 200,
        },
        {
            "label": _("Purchase Posting Date"),
            "fieldtype": "Date",
            "fieldname": "pi_posting_date",
            "width": 125,
        }
       
    ]

    return columns

def get_data(filters):
    query = """
        SELECT
            si.posting_date AS si_posting_date,
            si.customer_name AS customer_name,
            si.name AS sales_invoice,
            pi.status AS status,
            pi.supplier,   
            pi.name AS purchase_invoice_number,      
            (
                SELECT COUNT(pi.name)
                FROM
                    `tabPurchase Invoice` pi
                WHERE
                    pi.inter_company_invoice_reference = si.name
            ) AS connection,
            si.grand_total AS sales_grand_total,
            pi.grand_total AS purchase_grand_total,            
            si.modified_by AS si_modified_by,
            pi.modified_by AS pi_modified_by,
            pi.posting_date AS pi_posting_date,
            pi.docstatus            
            
        FROM
            `tabSales Invoice` si
        LEFT JOIN
            `tabPurchase Invoice` pi
        ON
            si.name = pi.inter_company_invoice_reference
        
        WHERE si.is_internal_customer = 1 AND si.docstatus != 2
    """

    conditions = []
    if filters.get("si_posting_date"):
        conditions.append("si.posting_date = %(si_posting_date)s")

    if filters.get("customer"):
        conditions.append("si.customer_name = %(customer)s")

    if filters.get("sales_invoice"):
        conditions.append("si.name = %(sales_invoice)s")

    if filters.get("supplier"):
        conditions.append("pi.supplier = %(supplier)s")
    
    if filters.get("Purchase_invoice_status") == "completed":
        conditions.append("pi.docstatus = 1")
    elif filters.get("Purchase_invoice_status") == "pending":
        conditions.append("(pi.docstatus IS NULL OR pi.docstatus = 0 )")
    elif filters.get("Purchase_invoice_status") == "cancelled":
        conditions.append("(pi.docstatus = 2 )")
    # else:
    #     conditions.append("(pi.docstatus IS NULL OR pi.docstatus <> 2 )")

    
    if conditions:
        query += " AND " + " AND ".join(conditions)     


    # Finalize query with grouping and ordering
    query += """
          GROUP BY
            si.name, si.customer_name, pi.name, pi.status
        ORDER BY
            si.creation DESC
    """

    raw_data = frappe.db.sql(query, filters, as_dict=True)

    last_sales_invoice = None
    last_customer_name = None

    for row in raw_data:

        if row['docstatus'] == 1:
            row['status'] = '<span class="indicator-pill green">Completed</span>'
        elif row['docstatus'] == 2:
            row['status'] = '<span class="indicator-pill red">Cancelled</span>'
        else:
            row['status'] = '<span class="indicator-pill yellow">Pending</span>'       


        if last_sales_invoice == row['sales_invoice'] and last_customer_name == row['customer_name']:
            row['si_posting_date'] = ''
            row['customer_name'] = ''
            row['sales_invoice'] = ''            
            row['connection'] = ''            
            row['si_modified_by'] = ''

        else:
            last_sales_invoice = row['sales_invoice']
            last_customer_name = row['customer_name']

        
        row['si_modified_by'] = frappe.db.get_value("User" , row['si_modified_by'] , "full_name")
        row['pi_modified_by'] = frappe.db.get_value("User" , row['pi_modified_by'] , "full_name")
        

    return raw_data

