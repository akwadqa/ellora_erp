// Copyright (c) 2025, Akwad Programming and contributors
// For license information, please see license.txt

frappe.query_reports["Inter Company Sales Invoice"] = {
	"filters": [
		{
			fieldname: "si_posting_date",
			label: __("Sales Invoice Posting Date"),
			fieldtype: "Date"
		},
		{
			fieldname: "customer",
			label: __("Customer"),
			fieldtype: "Link",
			options: "Customer",
			get_query: function() {
				return {
					filters: {
						"is_internal_customer": 1
					}
				};
			}
		},
		{
			fieldname: "supplier",
			label: __("Supplier"),
			fieldtype: "Link",
			options: "Supplier",
		},	
		{
			fieldname: "sales_invoice",
			label: __("Sales Invoice"),
			fieldtype: "Link",
			options: "Sales Invoice"
		},
		{
			fieldname: "Purchase_invoice_status",
			label: __("Purchase Invoice Status"),
			fieldtype: "Select",
			options: [
				"",
				{
					label: __("Completed"),
					value: "completed",
				},
				{
					label: __("Pending"),
					value: "pending",
				}				
			]
		},
	],

	
};
