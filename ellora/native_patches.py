from frappe.www import printview
from ellora import native_overrides

printview.get_rendered_template = native_overrides.custom_get_rendered_template

from erpnext.controllers import queries

queries.item_query = native_overrides.custom_item_query