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
		"against_account": _("Main Cash FS"),
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
		"against_account": _("Total"),
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
		"against_account": _("Closing (Opening + Total)"),
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
			gl.name AS name,
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

	gl_entry_list = frappe.db.sql(query, {"company": company, "account": account, "from_date": from_date, "to_date": to_date}, as_dict=1)

	final_data = []
	for gl_entry in gl_entry_list:
		if gl_entry["voucher_type"] == "Expense Entry":
			expense_entry_list = frappe.db.sql("""
				SELECT 
					expense_account, amount, notes
				FROM 
					`tabExpense Entry Detail`
				WHERE 
					parent = %s
			""", (gl_entry["voucher_no"]), as_dict=True)

			for expense_entry in expense_entry_list:
				final_data.append({
					"name": gl_entry["name"],
					"posting_date": gl_entry["posting_date"],
					"voucher_no": gl_entry["voucher_no"],
					"against_account": expense_entry["expense_account"],
					"debit": 0,
					"credit": expense_entry["amount"],
					"voucher_type": gl_entry["voucher_type"],
					"remarks": expense_entry["notes"]
				})
		else:
			final_data.append(gl_entry)

	return final_data


# def get_data(filters):
# 	company = filters.get("company")
# 	account = filters.get("account")
# 	from_date = filters.get("from_date")
# 	to_date = filters.get("to_date")

# 	where = "gl.account IN %(account)s AND gl.posting_date >= %(from_date)s AND gl.posting_date <= %(to_date)s AND is_cancelled = 0"
# 	if company:
# 		where = f"gl.company = %(company)s AND {where}"

# 	query = f""" 
# 		SELECT 
# 			gl.name AS name,
# 			gl.posting_date AS posting_date,
# 			gl.voucher_no AS voucher_no,
# 			gl.against AS against_account,
# 			gl.debit AS debit,
# 			gl.credit AS credit,
# 			gl.voucher_type AS voucher_type,
# 			gl.remarks AS remarks
# 		FROM 
# 			`tabGL Entry` gl
# 		WHERE 
# 			{where}
# 		ORDER BY 
# 			gl.posting_date, gl.account, gl.creation;
# 	"""

# 	gl_entry_list = frappe.db.sql(query, {"company": company, "account": account, "from_date": from_date, "to_date": to_date}, as_dict=1)

# 	frappe.log_error("gl_entry_list", gl_entry_list)

# 	# data = []
# 	# if gl_entry_list:
# 	# 	for gl_entry in gl_entry_list:
# 	# 		child_query = f""" 
# 	# 			SELECT 
# 	# 				gl.posting_date AS posting_date,
# 	# 				gl.voucher_no AS voucher_no,
# 	# 				gl.against AS against_account,
# 	# 				gl.debit AS debit,
# 	# 				gl.credit AS credit,
# 	# 				gl.voucher_type AS voucher_type,
# 	# 				gl.remarks AS remarks
# 	# 			FROM 
# 	# 				`tabGL Entry` gl
# 	# 			WHERE 
# 	# 				gl.voucher_no = %(voucher_no)s AND 
# 	# 				gl.name != %(name)s AND 
# 	# 				is_cancelled = 0
# 	# 			ORDER BY 
# 	# 				gl.posting_date, gl.account, gl.creation;
# 	# 		"""

# 	# 		child_gl_entry_list = frappe.db.sql(child_query, {"voucher_no": gl_entry.voucher_no, "name": gl_entry.name}, as_dict=1)
			
# 	# 		if child_gl_entry_list:
# 	# 			data.extend(child_gl_entry_list)
# 	# 		else:
# 	# 			data.append(gl_entry)
	
# 	# frappe.log_error("data", data)

# 	return gl_entry_list


def get_opening_balance(filters):
	company_filter = "company = %(company)s AND" if filters.get("company") else ""

	opening_balance = frappe.db.sql(f"""
		SELECT
			SUM(debit) AS debit, 
            SUM(credit) AS credit
		FROM
			`tabGL Entry`
		WHERE
			{company_filter}
			account IN %(account)s AND 
			(posting_date < %(from_date)s OR is_opening = 'Yes') AND 
			is_cancelled = 0
	""", {
		"company": filters.get("company"),
		"account": filters.get("account"),
		"from_date": filters.get("from_date"),
	}, as_dict=1)

	opening_balance = {
        "debit": (opening_balance[0].get("debit") or 0) if opening_balance else 0,
        "credit": (opening_balance[0].get("credit") or 0) if opening_balance else 0
    }

	frappe.log_error("opening_balance", opening_balance)

	return opening_balance


# def get_opening_balance(filters):
# 	company_filter = "company = %(company)s AND" if filters.get("company") else ""

# 	gl_entry_list = frappe.db.sql(f"""
# 		SELECT
# 			name, voucher_no, debit, credit
# 		FROM
# 			`tabGL Entry`
# 		WHERE
# 			{company_filter}
# 			account IN %(account)s AND 
# 			(posting_date < %(from_date)s OR is_opening = 'Yes') AND 
# 			is_cancelled = 0
# 	""", {
# 		"company": filters.get("company"),
# 		"account": filters.get("account"),
# 		"from_date": filters.get("from_date"),
# 	}, as_dict=1)

# 	opening_balance = {"debit": 0, "credit": 0}
# 	if gl_entry_list:
# 		for gl_entry in gl_entry_list:
# 			child_gl_entry_list = frappe.db.sql(f""" 
# 				SELECT 
# 					debit, credit
# 				FROM 
# 					`tabGL Entry` gl
# 				WHERE 
# 					gl.voucher_no = %(voucher_no)s AND 
# 					gl.name != %(name)s AND 
# 					is_cancelled = 0
# 			""", {
# 				"voucher_no": gl_entry.voucher_no, 
# 				"name": gl_entry.name
# 			}, as_dict=1)
			
# 			if child_gl_entry_list:
# 				for child_gl_entry in child_gl_entry_list:
# 					opening_balance["debit"] += child_gl_entry.get("debit", 0)
# 					opening_balance["credit"] += child_gl_entry.get("credit", 0)
# 			else:
# 				opening_balance["debit"] += gl_entry.get("debit", 0)
# 				opening_balance["credit"] += gl_entry.get("credit", 0)
			
# 	return opening_balance