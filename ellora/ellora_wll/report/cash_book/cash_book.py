# Copyright (c) 2025, Akwad Programming and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from erpnext import get_company_currency, get_default_company
from frappe.utils import flt


def execute(filters=None):
	if not filters.get("account"):
		frappe.throw(_("Please select an account."))

	columns, data = [], []

	columns = get_columns(filters)

	opening_balance = get_opening_balance(filters)
	balance = opening_balance["debit"] - opening_balance["credit"]
	opening_row = {
		"posting_date": None,
		"voucher_no": None,
		"against_account": "Opening",
		"debit": opening_balance["debit"],
		"credit": opening_balance["credit"],
		"balance": balance,
		"voucher_type": None,
		"remarks": None
	}
	data.append(opening_row)

	gl_entries = get_data(filters)

	for entry in gl_entries:
		balance += entry["debit"] - entry["credit"]

		entry.update({
			"balance": balance
		})
	
	data.extend(gl_entries)

	total_debit = 0.0
	total_credit = 0.0

	for entry in gl_entries:
		total_debit += flt(entry["debit"])
		total_credit += flt(entry["credit"])

	total_row = {
		"posting_date": None,
		"voucher_no": None,
		"against_account": "Total",
		"debit": total_debit,
		"credit": total_credit,
		"balance": None,
		"voucher_type": None,
		"remarks": None
	}
	data.append(total_row)

	closing_row = {
		"posting_date": None,
		"voucher_no": None,
		"against_account": "Closing (Opening + Total)",
		"debit": opening_balance["debit"] + total_debit,
		"credit": opening_balance["credit"] + total_credit,
		"balance": None,
		"voucher_type": None,
		"remarks": None
	}
	data.append(closing_row)

	return columns, data


def get_columns(filters):
	if filters.get("company"):
		currency = get_company_currency(filters["company"])
	else:
		company = get_default_company()
		currency = get_company_currency(company)

	columns = [
		{
			"label": _("Posting Date"), 
			"fieldname": "posting_date", 
			"fieldtype": "Date", 
			"width": 150,
			"align": "left"
		},
		{
			"label": _("Voucher No"),
			"fieldname": "voucher_no",
			"fieldtype": "Dynamic Link",
			"options": "voucher_type",
			"width": 200,
			"align": "left"
		},
		{
			"label": _("Against Account"),
			"fieldname": "against_account",
			"fieldtype": "Link",
			"options": "Account",
			"width": 200,
			"align": "left"
		},
		{
			"label": _("Debit ({0})").format(currency),
			"fieldname": "debit",
			"fieldtype": "Float",
			"width": 150
		},
		{
			"label": _("Credit ({0})").format(currency),
			"fieldname": "credit",
			"fieldtype": "Float",
			"width": 150
		},
		{
			"label": _("Balance ({0})").format(currency),
			"fieldname": "balance",
			"fieldtype": "Float",
			"width": 150
		},
		{
			"label": _("Voucher Type"), 
			"fieldname": "voucher_type", 
			"width": 150,
			"align": "left"
		},
		{
			"label": _("Remarks"), 
			"fieldname": "remarks", 
			"width": 400,
			"align": "left"
		}
	]

	return columns


def get_data(filters):
	company = filters.get("company")
	account = filters.get("account")
	from_date = filters.get("from_date")
	to_date = filters.get("to_date")

	where = "gl.account IN %(account)s AND gl.posting_date >= %(from_date)s AND gl.posting_date <= %(to_date)s AND is_cancelled = 0"
	if company:
		where = f"gl.company = %(company)s AND {where}"

	query = f""" 
		SELECT 
			gl.posting_date AS posting_date,
			gl.voucher_no AS voucher_no,
			gl.against AS against_account,
			gl.debit AS debit,
			gl.credit AS credit,
			gl.voucher_type AS voucher_type,
			gl.remarks AS remarks
		FROM 
			`tabGL Entry` gl
		WHERE 
			{where}
		ORDER BY 
			gl.posting_date, gl.account, gl.creation;
	"""

	data = frappe.db.sql(query, {"company": company, "account": account, "from_date": from_date, "to_date": to_date}, as_dict=1)

	frappe.log_error("data", data)
	return data


def get_opening_balance(filters):
	opening_balance = frappe.db.sql("""
		SELECT
			SUM(debit) AS total_debit,
			SUM(credit) AS total_credit
		FROM
			`tabGL Entry`
		WHERE
			company = %(company)s AND 
			account IN %(account)s AND 
			(posting_date < %(from_date)s OR is_opening = 'Yes') AND 
			is_cancelled = 0
	""", {
		"company": filters.get("company"),
		"account": filters.get("account"),
		"from_date": filters.get("from_date"),
	}, as_dict=1)

	if opening_balance and opening_balance[0]:
		return {
			"debit": flt(opening_balance[0].get("total_debit", 0)),
            "credit": flt(opening_balance[0].get("total_credit", 0))
		}
	else:
		return {"debit": 0, "credit": 0}