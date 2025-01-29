// Copyright (c) 2025, Akwad Programming and contributors
// For license information, please see license.txt

frappe.query_reports["Ellora Sales Register"] = {
	filters: [
		{
			fieldname: "from_datetime",
			label: __("From Date"),
			fieldtype: "Datetime",
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			width: "80",
		},
		{
			fieldname: "to_datetime",
			label: __("To Date"),
			fieldtype: "Datetime",
			default: frappe.datetime.get_today(),
		},
		{
			fieldname: "customer",
			label: __("Customer"),
			fieldtype: "Link",
			options: "Customer",
		},
		{
			fieldname: "customer_group",
			label: __("Customer Group"),
			fieldtype: "Link",
			options: "Customer Group",
		},
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
		},
		{
			fieldname: "mode_of_payment",
			label: __("Mode of Payment"),
			fieldtype: "Link",
			options: "Mode of Payment",
		},
		{
			fieldname: "owner",
			label: __("Owner"),
			fieldtype: "Link",
			options: "User",
		},
		{
			fieldname: "cost_center",
			label: __("Cost Center"),
			fieldtype: "Link",
			options: "Cost Center",
		},
		{
			fieldname: "warehouse",
			label: __("Warehouse"),
			fieldtype: "Link",
			options: "Warehouse",
		},
		{
			fieldname: "brand",
			label: __("Brand"),
			fieldtype: "Link",
			options: "Brand",
		},
		{
			fieldname: "item_group",
			label: __("Item Group"),
			fieldtype: "Link",
			options: "Item Group",
		},
		{
			fieldname: "include_payments",
			label: __("Show Ledger View"),
			fieldtype: "Check",
			default: 0,
		},
		{
			fieldname: "include_intercompany_sales",
			label: __("Include Intercompany Sales"),
			fieldtype: "Check",
			default: 0,
		},
		{
			fieldname: "include_return_sales",
			label: __("Include Return Sales"),
			fieldtype: "Check",
			default: 0,
		}
	],
};

erpnext.utils.add_dimensions("Ellora Sales Register", 7);
