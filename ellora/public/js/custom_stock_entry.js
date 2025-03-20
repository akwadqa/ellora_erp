frappe.ui.form.on("Stock Entry", {
    setup: function (frm) {
		["items"].forEach((d) => {
			frm.fields_dict[d].grid.get_field("uom").get_query = function (doc, cdt, cdn) {
				var row = locals[cdt][cdn];
				return {
					query: "ellora.api.get_item_uoms",
					filters: { value: row.item_code },
				};
			};
		});
	},

	posting_date: function(frm) {
        let today = frappe.datetime.get_today();
        let postingDate = frm.doc.posting_date;

        if (postingDate > today) {
            frappe.msgprint(__('Posting Date cannot be in the future.'));
            frm.set_value('posting_date', today);
        }
    }
})