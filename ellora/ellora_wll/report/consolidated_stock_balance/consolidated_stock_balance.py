# Copyright (c) 2025, Akwad Programming and contributors
# For license information, please see license.txt


import frappe
from frappe import _


def execute(filters=None):
	columns, data = [], []

	# Get all warehouses
	warehouse_filters = {}
	if filters.get("company"):
		warehouse_filters["company"] = filters["company"]
        
	warehouse_list = frappe.get_all(
		"Warehouse",
		filters=warehouse_filters,
		pluck="name"
	)

	columns = get_columns(warehouse_list)
	data = get_data(filters, warehouse_list)

	return columns, data


def get_columns(warehouse_list):
    columns = [
        {
			"label": _("Item Code"),
			"fieldname": "item_code",
			"fieldtype": "Data",
			"width": 150
        },
        {
            "label": _("Item Name"),
            "fieldname": "item_name",
            "fieldtype": "Data",
            "width": 200
        },
        {
            "label": _("UOM"),
            "fieldname": "uom",
            "fieldtype": "Data",
            "width": 100
        },
    ]
    
	# Dynamically add columns based on available warehouses
    for warehouse in warehouse_list:
        columns.append(
            {
                "label": _(warehouse),
                "fieldname": frappe.scrub(warehouse),
                "fieldtype": "Float",
                "width": 200
            }
        )
    
    columns.append(
        {
			"label": _("Total Stock"),
			"fieldname": "total_stock",
			"fieldtype": "Float",
			"width": 150
		}
    )
    
    columns.append(
        {
            "label": _("Valuation Rate"),
            "fieldname": "valuation_rate",
            "fieldtype": "Currency",
            "width": 150
        }
    )

    return columns


def get_data(filters, warehouse_list):
	# Prepare item filters
	item_filters = {}
	if filters.get("item"):
		item_filters["name"] = filters["item"]
	if filters.get("item_group"):
		item_filters["item_group"] = filters["item_group"]
	if filters.get("brand"):
		item_filters["brand"] = filters["brand"]

	# Fetch items based on filters
	item_list = frappe.get_all(
		"Item",
		filters=item_filters,
		fields=["name", "item_name"]
	)
	item_codes = [item["name"] for item in item_list]

	if not item_codes:
		return []  # No items match the filters

	# Fetch stock details from Bin
	query = """
		SELECT 
			bin.item_code, 
			bin.warehouse, 
			bin.actual_qty, 
			bin.stock_uom, 
			bin.valuation_rate
		FROM 
			`tabBin` bin
		WHERE 
			bin.item_code IN %(item_codes)s
			AND bin.warehouse IN %(warehouses)s
			AND bin.actual_qty > 0
	"""
	bin_data = frappe.db.sql(query, {"item_codes": item_codes, "warehouses": warehouse_list}, as_dict=True)

	# Organize data by item
	item_stock_map = {}

	for row in bin_data:
		item_code = row.item_code
		warehouse = row.warehouse
		actual_qty = row.actual_qty
		stock_uom = row.stock_uom
		valuation_rate = row.valuation_rate

		if item_code not in item_stock_map:
			# Initialize the item with default values
			item_stock_map[item_code] = {
				"item_code": item_code,
				"item_name": next((i["item_name"] for i in item_list if i["name"] == item_code), ""),
				"uom": stock_uom,
				"valuation_rate": valuation_rate,
				"total_stock": 0
			}
		
		# Store stock quantity for each warehouse
		item_stock_map[item_code][frappe.scrub(warehouse)] = actual_qty

		# Sum total stock
		item_stock_map[item_code]["total_stock"] += actual_qty

	# Convert to list format for report
	report_data = list(item_stock_map.values())
	frappe.log_error("item_stock_map", item_stock_map)
	frappe.log_error("report_data", report_data)
	return report_data