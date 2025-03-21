frappe.ui.form.on("Sales Order", {
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
})

frappe.ui.form.on("Sales Order Item", {
    item_code: function (frm, cdt, cdn) {
        frappe.model.set_value(cdt, cdn, "uom", null);
    }
});