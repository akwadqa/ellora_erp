import frappe
from frappe import _
from frappe.utils import cint
import json
from frappe.www.printview import validate_print_permission, get_print_format, standard_format, get_letter_head, convert_markdown, make_layout, trigger_print_script


def custom_get_rendered_template(
	doc: "Document",
	print_format: str | None = None,
	meta=None,
	no_letterhead: bool | None = None,
	letterhead: str | None = None,
	trigger_print: bool = False,
	settings=None,
):
	print_settings = frappe.get_single("Print Settings").as_dict()
	print_settings.update(settings or {})

	if isinstance(no_letterhead, str):
		no_letterhead = cint(no_letterhead)

	elif no_letterhead is None:
		no_letterhead = not cint(print_settings.with_letterhead)

	doc.flags.in_print = True
	doc.flags.print_settings = print_settings

	if not frappe.flags.ignore_print_permissions:
		validate_print_permission(doc)

	if doc.meta.is_submittable:
		if doc.docstatus.is_draft() and not cint(print_settings.allow_print_for_draft) and not doc.doctype == "Quotation":
			frappe.throw(_("Not allowed to print draft documents"), frappe.PermissionError)

		if doc.docstatus.is_cancelled() and not cint(print_settings.allow_print_for_cancelled):
			frappe.throw(_("Not allowed to print cancelled documents"), frappe.PermissionError)

	doc.run_method("before_print", print_settings)

	if not hasattr(doc, "print_heading"):
		doc.print_heading = None
	if not hasattr(doc, "sub_heading"):
		doc.sub_heading = None

	if not meta:
		meta = frappe.get_meta(doc.doctype)

	jenv = frappe.get_jenv()
	format_data, format_data_map = [], {}

	# determine template
	if print_format:
		doc.print_section_headings = print_format.show_section_headings
		doc.print_line_breaks = print_format.line_breaks
		doc.align_labels_right = print_format.align_labels_right
		doc.absolute_value = print_format.absolute_value

		def get_template_from_string():
			return jenv.from_string(get_print_format(doc.doctype, print_format))

		template = None
		if hook_func := frappe.get_hooks("get_print_format_template"):
			template = frappe.get_attr(hook_func[-1])(jenv=jenv, print_format=print_format)

		if template:
			pass
		elif print_format.custom_format:
			template = get_template_from_string()

		elif print_format.format_data:
			# set format data
			format_data = json.loads(print_format.format_data)
			for df in format_data:
				format_data_map[df.get("fieldname")] = df
				if "visible_columns" in df:
					for _df in df.get("visible_columns"):
						format_data_map[_df.get("fieldname")] = _df

			doc.format_data_map = format_data_map

			template = "standard"

		elif print_format.standard == "Yes":
			template = get_template_from_string()

		else:
			# fallback
			template = "standard"

	else:
		template = "standard"

	if template == "standard":
		template = jenv.get_template(standard_format)

	letter_head = frappe._dict(get_letter_head(doc, no_letterhead, letterhead) or {})

	if letter_head.content:
		letter_head.content = frappe.utils.jinja.render_template(letter_head.content, {"doc": doc.as_dict()})
		if letter_head.header_script:
			letter_head.content += f"""
				<script>
					{ letter_head.header_script }
				</script>
			"""

	if letter_head.footer:
		letter_head.footer = frappe.utils.jinja.render_template(letter_head.footer, {"doc": doc.as_dict()})
		if letter_head.footer_script:
			letter_head.footer += f"""
				<script>
					{ letter_head.footer_script }
				</script>
			"""

	convert_markdown(doc)

	args = {}
	# extract `print_heading_template` from the first field and remove it
	if format_data and format_data[0].get("fieldname") == "print_heading_template":
		args["print_heading_template"] = format_data.pop(0).get("options")

	args.update(
		{
			"doc": doc,
			"meta": frappe.get_meta(doc.doctype),
			"layout": make_layout(doc, meta, format_data),
			"no_letterhead": no_letterhead,
			"trigger_print": cint(trigger_print),
			"letter_head": letter_head.content,
			"footer": letter_head.footer,
			"print_settings": print_settings,
		}
	)
	hook_func = frappe.get_hooks("pdf_body_html")
	html = frappe.get_attr(hook_func[-1])(jenv=jenv, template=template, print_format=print_format, args=args)

	if cint(trigger_print):
		html += trigger_print_script

	return html





import frappe
import json
from frappe import scrub
from frappe.desk.reportview import get_filters_cond, get_match_cond
from frappe.utils import nowdate

@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def custom_item_query(doctype, txt, searchfield, start, page_len, filters, as_dict=False):
	frappe.log_error("filters", filters)

	def get_bin_qty(item_code, warehouse):
		bin_qty = frappe.db.sql(
			"""select actual_qty from `tabBin`
			where item_code = %s and warehouse = %s
			limit 1""",
			(item_code, warehouse),
			as_dict=1,
		)

		return bin_qty[0].actual_qty or 0 if bin_qty else 0
	
	warehouse = filters.pop('warehouse', None) if filters else None

	page_len = 50
	columns = ", tabItem.item_name"

	doctype = "Item"
	conditions = []

	if isinstance(filters, str):
		filters = json.loads(filters)

	# Get searchfields from meta and use in Item Link field query
	meta = frappe.get_meta(doctype, cached=True)
	searchfields = meta.get_search_fields()

	# columns = ""
	# extra_searchfields = [field for field in searchfields if field not in ["name", "description"]]

	# if extra_searchfields:
	# 	columns += ", " + ", ".join(extra_searchfields)

	# if "description" in searchfields:
	# 	columns += """, if(length(tabItem.description) > 40, \
	# 		concat(substr(tabItem.description, 1, 40), "..."), description) as description"""

	searchfields = searchfields + [
		field
		for field in [searchfield or "name", "item_code", "item_group", "item_name"]
		if field not in searchfields
	]
	searchfields = " or ".join([field + " like %(txt)s" for field in searchfields])

	if filters and isinstance(filters, dict):
		if filters.get("customer") or filters.get("supplier"):
			party = filters.get("customer") or filters.get("supplier")
			item_rules_list = frappe.get_all(
				"Party Specific Item",
				filters={"party": party},
				fields=["restrict_based_on", "based_on_value"],
			)

			filters_dict = {}
			for rule in item_rules_list:
				if rule["restrict_based_on"] == "Item":
					rule["restrict_based_on"] = "name"
				filters_dict[rule.restrict_based_on] = []

			for rule in item_rules_list:
				filters_dict[rule.restrict_based_on].append(rule.based_on_value)

			for filter in filters_dict:
				filters[scrub(filter)] = ["in", filters_dict[filter]]

			if filters.get("customer"):
				del filters["customer"]
			else:
				del filters["supplier"]
		else:
			filters.pop("customer", None)
			filters.pop("supplier", None)

	description_cond = ""
	if frappe.db.count(doctype, cache=True) < 50000:
		# scan description only if items are less than 50000
		description_cond = "or tabItem.description LIKE %(txt)s"

	item_query_result = frappe.db.sql(
		"""select
			tabItem.name {columns}
		from tabItem
		where tabItem.docstatus < 2
			and tabItem.disabled=0
			and tabItem.has_variants=0
			and (tabItem.end_of_life > %(today)s or ifnull(tabItem.end_of_life, '0000-00-00')='0000-00-00')
			and ({scond} or tabItem.item_code IN (select parent from `tabItem Barcode` where barcode LIKE %(txt)s)
				{description_cond})
			{fcond} {mcond}
		order by
			if(locate(%(_txt)s, name), locate(%(_txt)s, name), 99999),
			if(locate(%(_txt)s, item_name), locate(%(_txt)s, item_name), 99999),
			idx desc,
			name, item_name
		limit %(start)s, %(page_len)s """.format(
			columns=columns,
			scond=searchfields,
			fcond=get_filters_cond(doctype, filters, conditions).replace("%", "%%"),
			mcond=get_match_cond(doctype).replace("%", "%%"),
			description_cond=description_cond,
		),
		{
			"today": nowdate(),
			"txt": "%%%s%%" % txt,
			"_txt": txt.replace("%", ""),
			"start": start,
			"page_len": page_len,
		},
		as_dict=as_dict,
	)
	if warehouse:
		item_query_result = list(map(list, item_query_result))
		for index, item in enumerate(item_query_result):
			item_code = item[0]
			bin_qty = get_bin_qty(item_code, warehouse)

			# Only append the "Stock" string for the first 5 items
			if index < 5:
				stock = f"<b>Stock = {bin_qty or '0'}</b>"
				item.append(stock)

	return item_query_result