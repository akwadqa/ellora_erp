# Copyright (c) 2024, Akwad Programming and contributors
# For license information, please see license.txt

import frappe

from frappe import _

from erpnext.accounts.report.financial_statements import (
	# get_columns,
	# get_data,
	# get_filtered_list_for_consolidated_report,
	get_period_list,
)


def execute(filters=None):
	columns, data = [], []

	period_list = get_period_list(
		filters.from_fiscal_year,
		filters.to_fiscal_year,
		filters.period_start_date,
		filters.period_end_date,
		filters.filter_based_on,
		filters.periodicity,
		company=filters.company,
	)
	
	columns = get_columns(period_list)

	opening_balance = get_opening_balance(filters)

	income, income_total = get_income_data(filters, period_list, opening_balance)
	data.extend(income)

	# empty row
	empty_row = {"account": None, "row_total": None}
	for period in period_list:
		empty_row[period["key"]] = None
	data.append(empty_row)

	expense, expense_total = get_expense_data(filters, period_list, opening_balance)
	data.extend(expense)

	# empty row
	empty_row = {"account": None, "row_total": None}
	for period in period_list:
		empty_row[period["key"]] = None
	data.append(empty_row)

	gross_profit_loss = income_total - expense_total
	gross_profit_loss_row = {"account": frappe.bold("Gross Profit") if gross_profit_loss >= 0 else frappe.bold("Gross Loss"), "row_total": gross_profit_loss}
	for period in period_list:
		gross_profit_loss_row[period["key"]] = None
	data.append(gross_profit_loss_row)

	# empty row
	empty_row = {"account": None, "row_total": None}
	for period in period_list:
		empty_row[period["key"]] = None
	data.append(empty_row)

	net_profit_loss, net_profit_loss_total = get_net_profit_loss_data(filters, period_list, gross_profit_loss)
	data.extend(net_profit_loss)

	# empty row
	empty_row = {"account": None, "row_total": None}
	for period in period_list:
		empty_row[period["key"]] = None
	data.append(empty_row)

	net_profit_loss_row = {"account": frappe.bold("Net Profit") if net_profit_loss_total >= 0 else frappe.bold("Net Loss"), "row_total": net_profit_loss_total}
	for period in period_list:
		net_profit_loss_row[period["key"]] = None
	data.append(net_profit_loss_row)

	frappe.log_error("filters", filters)
	frappe.log_error("period_list", period_list)
	frappe.log_error("columns", columns)
	frappe.log_error("data", data)

	return columns, data


def get_columns(period_list):
	columns = [
		{
			"fieldname": "account",
			"label": _("Account"),
			"fieldtype": "Data",
			# "fieldtype": "Link",
			# "options": "Account",
			"width": 300,
		}
	]
	# if company:
	# 	columns.append(
	# 		{
	# 			"fieldname": "currency",
	# 			"label": _("Currency"),
	# 			"fieldtype": "Link",
	# 			"options": "Currency",
	# 			"hidden": 1,
	# 		}
	# 	)
	for period in period_list:
		columns.append(
			{
				"fieldname": period.key,
				"label": period.label,
				"fieldtype": "Currency",
				"options": "currency",
				"width": 150,
			}
		)
	columns.append(
		{
			"fieldname": "row_total",
			"label": _("Total"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 150,
		}
	)

	return columns


def get_opening_balance(filters):
	opening_balance = frappe.db.sql("""
		SELECT
			(SUM(gle.debit) - SUM(gle.credit)) AS balance
		FROM
			`tabGL Entry` AS gle
		INNER JOIN
			`tabAccount` AS acc
		ON
			gle.account = acc.name
		WHERE
			gle.company = %(company)s
			AND acc.account_type = 'Stock'
			AND (gle.posting_date < %(period_start_date)s OR gle.is_opening = 'Yes')
	""", {
		"company": filters.company,
		"period_start_date": filters.period_start_date,
	}, as_dict=True)

	return opening_balance[0]["balance"] if opening_balance and opening_balance[0]["balance"] else 0


def get_income_data(filters, period_list, opening_balance):
	income = []

	first_row = {"account": frappe.bold("Proceeds from Sales"), "row_total": None}
	for period in period_list:
		first_row[period["key"]] = None
	income.append(first_row)

	sales_data = get_sales_data(filters, period_list)
	income.append(sales_data)

	sales_return_data = get_sales_return_data(filters, period_list)
	income.append(sales_return_data)

	direct_income_data = get_direct_income_data(filters, period_list)
	income.append(direct_income_data)

	opening_balance_row = {"account": "Closing Balance", "row_total": opening_balance}
	for period in period_list:
		opening_balance_row[period["key"]] = None
	income.append(opening_balance_row)

	last_row_total = sales_data['row_total'] - sales_return_data['row_total'] + direct_income_data['row_total'] + opening_balance_row['row_total']
	last_row = {"account": "Total", "row_total": last_row_total}
	for period in period_list:
		last_row[period["key"]] = None
	income.append(last_row)

	return income, last_row_total


def get_sales_data(filters, period_list):
	# Initialize sales data row
	sales_data = {"account": "Sales"}
    
	total_sales = 0

	base_filters = {
		"company": filters.get("company"),
		"voucher_type": "Sales Invoice",
		"voucher_subtype": "Debit Note",
	}
	if filters.get("branch") and len(filters.get("branch")) > 0:
		base_filters["branch"] = ["in", filters.get("branch")]
    
	for period in period_list:
		period_filters = base_filters.copy()
		period_filters["posting_date"] = ["between", [period["from_date"], period["to_date"]]]
		
		# Fetch GL Entry totals for this period
		sales_total = frappe.get_all(
			"GL Entry",
			filters=period_filters,
			fields=["SUM(debit) as total"]
		)
		
		period_sales_total = sales_total[0].total if sales_total and sales_total[0].total else 0

		# Add the total to the corresponding period key
		sales_data[period["key"]] = period_sales_total
		# Accumulate the total sales for all periods
		total_sales += period_sales_total
	
	sales_data["row_total"] = total_sales

	return sales_data


def get_sales_return_data(filters, period_list):
	# Initialize sales return data row
	sales_return_data = {"account": "Sales Return"}

	total_sales_return = 0

	base_filters = {
		"company": filters.get("company"),
		"voucher_type": "Sales Invoice",
		"voucher_subtype": "Credit Note",
	}
	if filters.get("branch") and len(filters.get("branch")) > 0:
		base_filters["branch"] = ["in", filters.get("branch")]
	
	for period in period_list:
		period_filters = base_filters.copy()
		period_filters["posting_date"] = ["between", [period["from_date"], period["to_date"]]]
	
		# Fetch GL Entry totals for this period
		sales_return_total = frappe.get_all(
			"GL Entry",
			filters=period_filters,
			fields=["SUM(credit) as total"]
		)
		
		period_sales_return_total = sales_return_total[0].total if sales_return_total and sales_return_total[0].total else 0

		# Add the total to the corresponding period key
		sales_return_data[period["key"]] = period_sales_return_total
		# Accumulate the total sales return for all periods
		total_sales_return += period_sales_return_total
	
	sales_return_data["row_total"] = total_sales_return

	return sales_return_data


def get_direct_income_data(filters, period_list):
	# Initialize direct income data row
	direct_income_data = {"account": "Direct Income"}

	total_direct_income = 0

	# Fetch all accounts with account_type = 'Direct Income'
	direct_income_accounts = frappe.get_all(
		"Account",
		filters={"account_type": "Direct Income", "company": filters.get("company")},
		pluck="name"
	)

	base_filters = {
		"company": filters.get("company"),
		"account": ["in", direct_income_accounts],
	}
	if filters.get("branch") and len(filters.get("branch")) > 0:
		base_filters["branch"] = ["in", filters.get("branch")]
	
	for period in period_list:
		period_filters = base_filters.copy()
		period_filters["posting_date"] = ["between", [period["from_date"], period["to_date"]]]
	
		# Fetch GL Entry totals for this period
		direct_income_total = frappe.get_all(
			"GL Entry",
			filters=period_filters,
			fields=["SUM(credit) - SUM(debit) as total"]
		)
		
		period_direct_income_total = direct_income_total[0].total if direct_income_total and direct_income_total[0].total else 0

		# Add the total to the corresponding period key
		direct_income_data[period["key"]] = period_direct_income_total
		# Accumulate the total direct income for all periods
		total_direct_income += period_direct_income_total
	
	direct_income_data["row_total"] = total_direct_income

	return direct_income_data




def get_expense_data(filters, period_list, opening_balance):
	expense = []

	first_row = {"account": frappe.bold("Cost of Sales"), "row_total": None}
	for period in period_list:
		first_row[period["key"]] = None
	expense.append(first_row)

	purchase_data = get_purchase_data(filters, period_list)
	expense.append(purchase_data)

	purchase_return_data = get_purchase_return_data(filters, period_list)
	expense.append(purchase_return_data)

	direct_expense_data = get_direct_expense_data(filters, period_list)
	expense.append(direct_expense_data)

	opening_balance_row = {"account": "Opening Balance", "row_total": opening_balance}
	for period in period_list:
		opening_balance_row[period["key"]] = None
	expense.append(opening_balance_row)

	last_row_total = purchase_data['row_total'] - purchase_return_data['row_total'] + direct_expense_data['row_total'] + opening_balance_row['row_total']
	last_row = {"account": "Total", "row_total": last_row_total}
	for period in period_list:
		last_row[period["key"]] = None
	expense.append(last_row)

	return expense, last_row_total


def get_purchase_data(filters, period_list):
	# Initialize purchase data row
	purchase_data = {"account": "Purchase"}
    
	total_purchase = 0

	base_filters = {
		"company": filters.get("company"),
		"voucher_type": "Purchase Invoice",
		"voucher_subtype": "Credit Note",
	}
	if filters.get("branch") and len(filters.get("branch")) > 0:
		base_filters["branch"] = ["in", filters.get("branch")]
    
	for period in period_list:
		period_filters = base_filters.copy()
		period_filters["posting_date"] = ["between", [period["from_date"], period["to_date"]]]
		
		# Fetch GL Entry totals for this period
		purchase_total = frappe.get_all(
			"GL Entry",
			filters=period_filters,
			fields=["SUM(credit) as total"]
		)
		
		period_purchases_total = purchase_total[0].total if purchase_total and purchase_total[0].total else 0

		# Add the total to the corresponding period key
		purchase_data[period["key"]] = period_purchases_total
		# Accumulate the total purchase for all periods
		total_purchase += period_purchases_total
	
	purchase_data["row_total"] = total_purchase

	return purchase_data


def get_purchase_return_data(filters, period_list):
	# Initialize sales return data row
	purchase_return_data = {"account": "Purchase Return"}

	total_purchase_return = 0

	base_filters = {
		"company": filters.get("company"),
		"voucher_type": "Purchase Invoice",
		"voucher_subtype": "Debit Note",
	}
	if filters.get("branch") and len(filters.get("branch")) > 0:
		base_filters["branch"] = ["in", filters.get("branch")]
	
	for period in period_list:
		period_filters = base_filters.copy()
		period_filters["posting_date"] = ["between", [period["from_date"], period["to_date"]]]
	
		# Fetch GL Entry totals for this period
		purchase_return_total = frappe.get_all(
			"GL Entry",
			filters=period_filters,
			fields=["SUM(debit) as total"]
		)
		
		period_purchase_return_total = purchase_return_total[0].total if purchase_return_total and purchase_return_total[0].total else 0

		# Add the total to the corresponding period key
		purchase_return_data[period["key"]] = period_purchase_return_total
		# Accumulate the total purchase return for all periods
		total_purchase_return += period_purchase_return_total
	
	purchase_return_data["row_total"] = total_purchase_return

	return purchase_return_data


def get_direct_expense_data(filters, period_list):
	# Initialize direct expense data row
	direct_expense_data = {"account": "Direct Expense"}

	total_direct_expense = 0

	# Fetch all accounts with account_type = 'Direct Income'
	direct_expense_accounts = frappe.get_all(
		"Account",
		filters={"account_type": "Direct Expense", "company": filters.get("company")},
		pluck="name"
	)

	base_filters = {
		"company": filters.get("company"),
		"account": ["in", direct_expense_accounts],
	}
	if filters.get("branch") and len(filters.get("branch")) > 0:
		base_filters["branch"] = ["in", filters.get("branch")]
	
	for period in period_list:
		period_filters = base_filters.copy()
		period_filters["posting_date"] = ["between", [period["from_date"], period["to_date"]]]
	
		# Fetch GL Entry totals for this period
		direct_expense_total = frappe.get_all(
			"GL Entry",
			filters=period_filters,
			fields=["SUM(debit) - SUM(credit) as total"]
		)
		
		period_direct_expense_total = direct_expense_total[0].total if direct_expense_total and direct_expense_total[0].total else 0

		# Add the total to the corresponding period key
		direct_expense_data[period["key"]] = period_direct_expense_total
		# Accumulate the total direct expense for all periods
		total_direct_expense += period_direct_expense_total
	
	direct_expense_data["row_total"] = total_direct_expense

	return direct_expense_data



def get_net_profit_loss_data(filters, period_list, gross_profit_loss):
	net_profit_loss = []

	# income
	income_row = {"account": frappe.bold("Income"), "row_total": None}
	for period in period_list:
		income_row[period["key"]] = None
	net_profit_loss.append(income_row)

	gross_loss_row = {"account": "Gross Loss", "row_total": gross_profit_loss if gross_profit_loss < 0 else 0}
	for period in period_list:
		gross_loss_row[period["key"]] = None
	net_profit_loss.append(gross_loss_row)

	indirect_income_data = get_indirect_income_data(filters, period_list)
	net_profit_loss.append(indirect_income_data)

	income_total = gross_loss_row['row_total'] + indirect_income_data['row_total']
	income_total_row = {"account": "Total", "row_total": income_total}
	for period in period_list:
		income_total_row[period["key"]] = None
	net_profit_loss.append(income_total_row)

	# empty row
	empty_row = {"account": None, "row_total": None}
	for period in period_list:
		empty_row[period["key"]] = None
	net_profit_loss.append(empty_row)

	# expense
	expense_row = {"account": frappe.bold("Expense"), "row_total": None}
	for period in period_list:
		expense_row[period["key"]] = None
	net_profit_loss.append(expense_row)

	gross_profit_row = {"account": "Gross Profit", "row_total": gross_profit_loss if gross_profit_loss >= 0 else 0}
	for period in period_list:
		gross_profit_row[period["key"]] = None
	net_profit_loss.append(gross_profit_row)

	indirect_expense_data = get_indirect_expense_data(filters, period_list)
	net_profit_loss.append(indirect_expense_data)

	expense_total = gross_profit_row['row_total'] + indirect_expense_data['row_total']
	expense_total_row = {"account": "Total", "row_total": expense_total}
	for period in period_list:
		expense_total_row[period["key"]] = None
	net_profit_loss.append(expense_total_row)

	net_profit_loss_total = income_total - expense_total

	return net_profit_loss, net_profit_loss_total


def get_indirect_income_data(filters, period_list):
	# Initialize indirect income data row
	indirect_income_data = {"account": "Indirect Income"}

	total_indirect_income = 0

	# Fetch all accounts with account_type = 'Indirect Income'
	indirect_income_accounts = frappe.get_all(
		"Account",
		filters={"account_type": "Indirect Income", "company": filters.get("company")},
		pluck="name"
	)

	base_filters = {
		"company": filters.get("company"),
		"account": ["in", indirect_income_accounts],
	}
	if filters.get("branch") and len(filters.get("branch")) > 0:
		base_filters["branch"] = ["in", filters.get("branch")]
	
	for period in period_list:
		period_filters = base_filters.copy()
		period_filters["posting_date"] = ["between", [period["from_date"], period["to_date"]]]
	
		# Fetch GL Entry totals for this period
		indirect_income_total = frappe.get_all(
			"GL Entry",
			filters=period_filters,
			fields=["SUM(credit) - SUM(debit) as total"]
		)
		
		period_indirect_income_total = indirect_income_total[0].total if indirect_income_total and indirect_income_total[0].total else 0

		# Add the total to the corresponding period key
		indirect_income_data[period["key"]] = period_indirect_income_total
		# Accumulate the total indirect income for all periods
		total_indirect_income += period_indirect_income_total
	
	indirect_income_data["row_total"] = total_indirect_income

	return indirect_income_data


def get_indirect_expense_data(filters, period_list):
	# Initialize indirect expense data row
	indirect_expense_data = {"account": "Indirect Expense"}

	total_indirect_expense = 0

	# Fetch all accounts with account_type = 'Indirect Expense'
	indirect_expense_accounts = frappe.get_all(
		"Account",
		filters={"account_type": "Indirect Expense", "company": filters.get("company")},
		pluck="name"
	)

	base_filters = {
		"company": filters.get("company"),
		"account": ["in", indirect_expense_accounts],
	}
	if filters.get("branch") and len(filters.get("branch")) > 0:
		base_filters["branch"] = ["in", filters.get("branch")]
	
	for period in period_list:
		period_filters = base_filters.copy()
		period_filters["posting_date"] = ["between", [period["from_date"], period["to_date"]]]
	
		# Fetch GL Entry totals for this period
		indirect_expense_total = frappe.get_all(
			"GL Entry",
			filters=period_filters,
			fields=["SUM(debit) - SUM(credit) as total"]
		)
		
		period_indirect_expense_total = indirect_expense_total[0].total if indirect_expense_total and indirect_expense_total[0].total else 0

		# Add the total to the corresponding period key
		indirect_expense_data[period["key"]] = period_indirect_expense_total
		# Accumulate the total indirect expense for all periods
		total_indirect_expense += period_indirect_expense_total
	
	indirect_expense_data["row_total"] = total_indirect_expense

	return indirect_expense_data