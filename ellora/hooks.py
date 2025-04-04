app_name = "ellora"
app_title = "Ellora WLL"
app_publisher = "Akwad Programming"
app_description = "Holds all customizations of Ellora ERP."
app_email = "support@akwad.qa"
app_license = "mit"
# required_apps = []

# Includes in <head>
# ------------------
#fixtures = [
#    {"dt": "Property Setter", "filters": [["module", "=", "Ellora WLL"]]},
#    {"dt": "Custom Field", "filters": [["module", "=", "Ellora WLL"]]}
#    ]
# include js, css files in header of desk.html
# app_include_css = "/assets/ellora/css/ellora.css"
app_include_js = "/assets/ellora/js/custom_shortcuts.js"

# include js, css files in header of web template
# web_include_css = "/assets/ellora/css/ellora.css"
# web_include_js = "/assets/ellora/js/ellora.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "ellora/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
    "Sales Invoice" : "public/js/custom_sales_invoice.js",
    "Purchase Invoice" : "public/js/custom_purchase_invoice.js",
    "Quotation": "public/js/custom_quotation.js",
    "Delivery Note": "public/js/custom_delivery_note.js",
    "Purchase Order": "public/js/custom_purchase_order.js",
    "Sales Order": "public/js/custom_sales_order.js",
    "Supplier Quotation": "public/js/custom_supplier_quotation.js",
    "Material Request": "public/js/custom_material_request.js",
    "Purchase Receipt": "public/js/custom_purchase_receipt.js",
    "Stock Entry": "public/js/custom_stock_entry.js",
}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "ellora/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "ellora.utils.jinja_methods",
# 	"filters": "ellora.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "ellora.install.before_install"
# after_install = "ellora.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "ellora.uninstall.before_uninstall"
# after_uninstall = "ellora.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "ellora.utils.before_app_install"
# after_app_install = "ellora.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "ellora.utils.before_app_uninstall"
# after_app_uninstall = "ellora.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "ellora.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

override_doctype_class = {
	# "ToDo": "custom_app.overrides.CustomToDo",
    "Bank Clearance": "ellora.overrides.CustomBankClearance"
}

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Quotation": {
        "validate": "ellora.hooks_call.validate_minimum_selling_rate"
	},
    "Sales Order": {
        "validate": "ellora.hooks_call.validate_minimum_selling_rate"
	},
    "Sales Invoice": {
        "validate": "ellora.hooks_call.validate_minimum_selling_rate",
        "before_validate": "ellora.hooks_call.uncheck_update_stock"
	},
    "Delivery Note": {
        "validate": "ellora.hooks_call.validate_minimum_selling_rate"
	},
    "Purchase Receipt": {
        "before_insert": "ellora.hooks_call.clear_warehouse_fields"
    }
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"ellora.tasks.all"
# 	],
# 	"daily": [
# 		"ellora.tasks.daily"
# 	],
# 	"hourly": [
# 		"ellora.tasks.hourly"
# 	],
# 	"weekly": [
# 		"ellora.tasks.weekly"
# 	],
# 	"monthly": [
# 		"ellora.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "ellora.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	# "frappe.desk.doctype.event.event.get_events": "ellora.event.get_events",
#     "erpnext.accounts.doctype.bank_clearance.bank_clearance.update_clearance_date": "ellora.overrides.custom_update_clearance_date"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "ellora.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["ellora.utils.before_request"]
# after_request = ["ellora.utils.after_request"]

# Job Events
# ----------
# before_job = ["ellora.utils.before_job"]
# after_job = ["ellora.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"ellora.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

