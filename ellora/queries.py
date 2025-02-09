import frappe
from erpnext.controllers.queries import get_fields
from frappe.desk.reportview import get_filters_cond, get_match_cond


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def custom_get_delivery_notes_to_be_billed(doctype, txt, searchfield, start, page_len, filters, as_dict):
	doctype = "Delivery Note"
	fields = get_fields(doctype, ["name", "customer", "posting_date", "custom_cash_customer_name"])

	return frappe.db.sql(
		"""
		select {fields}
		from `tabDelivery Note`
		where `tabDelivery Note`.`{key}` like {txt} and
			`tabDelivery Note`.docstatus = 1
			and status not in ('Stopped', 'Closed') {fcond}
			and (
				(`tabDelivery Note`.is_return = 0 and `tabDelivery Note`.per_billed < 100)
				or (`tabDelivery Note`.grand_total = 0 and `tabDelivery Note`.per_billed < 100)
				or (
					`tabDelivery Note`.is_return = 1
					and return_against in (select name from `tabDelivery Note` where per_billed < 100)
				)
			)
			{mcond} order by `tabDelivery Note`.`{key}` asc limit {page_len} offset {start}
	""".format(
			fields=", ".join([f"`tabDelivery Note`.{f}" for f in fields]),
			key=searchfield,
			fcond=get_filters_cond(doctype, filters, []),
			mcond=get_match_cond(doctype),
			start=start,
			page_len=page_len,
			txt="%(txt)s",
		),
		{"txt": ("%%%s%%" % txt)},
		as_dict=as_dict,
	)