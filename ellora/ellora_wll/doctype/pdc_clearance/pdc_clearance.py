# Copyright (c) 2024, Akwad Programming and contributors
# For license information, please see license.txt


import frappe
from frappe import _, msgprint
from frappe.model.document import Document
from frappe.utils import flt, fmt_money, getdate

import erpnext



class PDCClearance(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from erpnext.accounts.doctype.bank_clearance_detail.bank_clearance_detail import (
			BankClearanceDetail,
		)

		account: DF.Link
		account_currency: DF.Link | None
		bank_account: DF.Link | None
		from_date: DF.Date
		payment_entries: DF.Table[BankClearanceDetail]
		to_date: DF.Date
	# end: auto-generated types

	@frappe.whitelist()
	def get_payment_entries(self):
		if not (self.from_date and self.to_date):
			frappe.throw(_("From Date and To Date are Mandatory"))

		if not self.account:
			frappe.throw(_("Account is mandatory to get payment entries"))

		entries = []

		method_name = "ellora.ellora_wll.doctype.pdc_clearance.pdc_clearance.get_payment_entries_for_bank_clearance"
		entries += (
			frappe.get_attr(method_name)(
				self.from_date,
				self.to_date,
				self.account,
				self.bank_account
			)
			or []
		)

		entries = sorted(
			entries,
			key=lambda k: getdate(k["posting_date"]),
		)

		self.set("payment_entries", [])
		default_currency = erpnext.get_default_currency()

		for d in entries:
			row = self.append("payment_entries", {})

			amount = flt(d.get("debit", 0)) - flt(d.get("credit", 0))

			if not d.get("account_currency"):
				d.account_currency = default_currency

			formatted_amount = fmt_money(abs(amount), 2, d.account_currency)
			d.amount = formatted_amount + " " + (_("Dr") if amount > 0 else _("Cr"))
			d.posting_date = getdate(d.posting_date)

			d.pop("credit")
			d.pop("debit")
			d.pop("account_currency")
			row.update(d)

	@frappe.whitelist()
	def update_clearance_date(self):
		clearance_date_updated = False
		for d in self.get("payment_entries"):
			if d.clearance_date:
				if not d.payment_document:
					frappe.throw(_("Row #{0}: Payment document is required to complete the transaction"))

				if d.cheque_date and getdate(d.clearance_date) < getdate(d.cheque_date):
					frappe.throw(
						_("Row #{0}: Clearance date {1} cannot be before Cheque Date {2}").format(
							d.idx, d.clearance_date, d.cheque_date
						)
					)

			if d.clearance_date:
				if not d.clearance_date:
					d.clearance_date = None

				payment_entry = frappe.get_doc(d.payment_document, d.payment_entry)
				payment_entry.clearance_date = d.clearance_date
				payment_entry.save()
				payment_entry.submit()

				clearance_date_updated = True

		if clearance_date_updated:
			self.get_payment_entries()
			msgprint(_("Clearance Date updated"))
		else:
			msgprint(_("Clearance Date not mentioned"))


def get_payment_entries_for_bank_clearance(
	from_date, to_date, account, bank_account
):
	entries = []

	if bank_account:
		condition += "and bank_account = %(bank_account)s"

	payment_entries = frappe.db.sql(
		f"""
			select
				"Payment Entry" as payment_document, name as payment_entry,
				reference_no as cheque_number, reference_date as cheque_date,
				if(paid_from=%(account)s, paid_amount + total_taxes_and_charges, 0) as credit,
				if(paid_from=%(account)s, 0, received_amount) as debit,
				posting_date, ifnull(party,if(paid_from=%(account)s,paid_to,paid_from)) as against_account, clearance_date,
				if(paid_to=%(account)s, paid_to_account_currency, paid_from_account_currency) as account_currency
			from `tabPayment Entry`
			where
				docstatus=0 and custom_cheque_status='Open'
				and (paid_from=%(account)s or paid_to=%(account)s)
				and posting_date >= %(from)s and posting_date <= %(to)s
				and (clearance_date IS NULL or clearance_date='0000-00-00')
			order by
				posting_date ASC, name DESC
		""",
		{
			"account": account,
			"from": from_date,
			"to": to_date,
			"bank_account": bank_account,
		},
		as_dict=1,
	)

	entries = (
		list(payment_entries)
	)
	
	return entries
