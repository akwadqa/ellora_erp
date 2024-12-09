// Copyright (c) 2024, Akwad Programming and contributors
// For license information, please see license.txt

frappe.query_reports["Trading P&L Report"] = {
	"filters": [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
			reqd: 1,
		},
		{
			fieldname: "filter_based_on",
			label: __("Filter Based On"),
			fieldtype: "Select",
			options: ["Fiscal Year", "Date Range"],
			default: ["Fiscal Year"],
			reqd: 1,
			on_change: function () {
				let filter_based_on = frappe.query_report.get_filter_value("filter_based_on");
				frappe.query_report.toggle_filter_display(
					"from_fiscal_year",
					filter_based_on === "Date Range"
				);
				frappe.query_report.toggle_filter_display("to_fiscal_year", filter_based_on === "Date Range");
				frappe.query_report.toggle_filter_display(
					"period_start_date",
					filter_based_on === "Fiscal Year"
				);
				frappe.query_report.toggle_filter_display(
					"period_end_date",
					filter_based_on === "Fiscal Year"
				);

				// Clear fiscal years and period dates when switching back to "Fiscal Year"
				if (filter_based_on === "Fiscal Year") {
					frappe.query_report.set_filter_value({
						from_fiscal_year: "",
						to_fiscal_year: "",
						period_start_date: "",
						period_end_date: "",
					});
				}

				// frappe.query_report.refresh();
			},
		},
		{
			fieldname: "period_start_date",
			label: __("Start Date"),
			fieldtype: "Date",
			hidden: 1,
			reqd: 1,
		},
		{
			fieldname: "period_end_date",
			label: __("End Date"),
			fieldtype: "Date",
			hidden: 1,
			reqd: 1,
		},
		{
			fieldname: "from_fiscal_year",
			label: __("Start Year"),
			fieldtype: "Link",
			options: "Fiscal Year",
			default: erpnext.utils.get_fiscal_year(frappe.datetime.get_today()),
			reqd: 1,
			on_change: () => {
				frappe.model.with_doc(
					"Fiscal Year",
					frappe.query_report.get_filter_value("from_fiscal_year"),
					function (r) {
						let year_start_date = frappe.model.get_value(
							"Fiscal Year",
							frappe.query_report.get_filter_value("from_fiscal_year"),
							"year_start_date"
						);
						frappe.query_report.set_filter_value({
							period_start_date: year_start_date,
						});
					}
				);
			},
		},
		{
			fieldname: "to_fiscal_year",
			label: __("End Year"),
			fieldtype: "Link",
			options: "Fiscal Year",
			default: erpnext.utils.get_fiscal_year(frappe.datetime.get_today()),
			reqd: 1,
			on_change: () => {
				frappe.model.with_doc(
					"Fiscal Year",
					frappe.query_report.get_filter_value("to_fiscal_year"),
					function (r) {
						let year_end_date = frappe.model.get_value(
							"Fiscal Year",
							frappe.query_report.get_filter_value("to_fiscal_year"),
							"year_end_date"
						);
						frappe.query_report.set_filter_value({
							period_end_date: year_end_date,
						});
					}
				);
			},
		},
		{
			fieldname: "periodicity",
			label: __("Periodicity"),
			fieldtype: "Select",
			options: [
				{ value: "Monthly", label: __("Monthly") },
				{ value: "Quarterly", label: __("Quarterly") },
				{ value: "Half-Yearly", label: __("Half-Yearly") },
				{ value: "Yearly", label: __("Yearly") },
			],
			default: "Yearly",
			reqd: 1,
		},
		{
			fieldname: "branch",
			label: __("Branch"),
			fieldtype: "MultiSelectList",
			get_data: function (txt) {
				return frappe.db.get_link_options("Branch", txt);
			},
		},
	],
	
	"onload": function () {
		// Trigger on_change for default fiscal years
		let from_fiscal_year = frappe.query_report.get_filter_value("from_fiscal_year");
		let to_fiscal_year = frappe.query_report.get_filter_value("to_fiscal_year");

		// Simulate the on_change logic
		if (from_fiscal_year) {
			frappe.model.with_doc("Fiscal Year", from_fiscal_year, function (r) {
				let year_start_date = frappe.model.get_value("Fiscal Year", from_fiscal_year, "year_start_date");
				frappe.query_report.set_filter_value({
					period_start_date: year_start_date,
				});
			});
		}

		if (to_fiscal_year) {
			frappe.model.with_doc("Fiscal Year", to_fiscal_year, function (r) {
				let year_end_date = frappe.model.get_value("Fiscal Year", to_fiscal_year, "year_end_date");
				frappe.query_report.set_filter_value({
					period_end_date: year_end_date,
				});
			});
		}
	},
};
