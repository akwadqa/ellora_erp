# Copyright (c) 2025, Akwad Programming and contributors
# For license information, please see license.txt


from ellora.ellora_wll.report.ellora_accounts_receivable.ellora_accounts_receivable import ReceivablePayableReport


def execute(filters=None):
	args = {
		"account_type": "Payable",
		"naming_by": ["Buying Settings", "supp_master_name"],
	}
	return ReceivablePayableReport(filters).run(args)
