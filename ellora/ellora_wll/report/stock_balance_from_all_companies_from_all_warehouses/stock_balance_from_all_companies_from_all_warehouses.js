// Copyright (c) 2025, Akwad Programming and contributors
// For license information, please see license.txt

frappe.query_reports["Stock Balance from All Companies from All Warehouses"] = {
    "filters": [
        {
            fieldname: "item",
            label: __("Item"),
            fieldtype: "Link",
            options: "Item"
        },
        {
            fieldname: "item_group",
            label: __("Item Group"),
            fieldtype: "Link",
            options: "Item Group"
        },
        {
            fieldname: "company",
            label: __("Company"),
            fieldtype: "Link",
            options: "Company",
			default: frappe.defaults.get_user_default("Company")
        },
        {
            fieldname: "brand",
            label: __("Brand"),
            fieldtype: "Link",
            options: "Brand"
        }
    ]
};
