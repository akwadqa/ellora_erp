frappe.ui.form.on("Purchase Receipt Item", "custom_stock_info", function(frm, cdt, cdn) {
    let child_doc = locals[cdt][cdn];
    let item_code = child_doc.item_code;

	const dialog = new frappe.ui.Dialog({
        title: __('Stock Monitor'),
        size: "extra-large",
        fields: [
            {
                fieldname: 'item',
                label: __('Item'),
                fieldtype: 'Link',
                options: 'Item',
                reqd: 0,
                default: item_code,
                change: function() {
                    get_stock_info(dialog.get_value('item'), dialog.get_value('uom'), dialog);
                }
            },
            {
                fieldname: 'uom',
                label: __('UOM'),
                fieldtype: 'Link',
                options: 'UOM',
                reqd: 0,
                change: function() {
                    get_stock_info(dialog.get_value('item'), dialog.get_value('uom'), dialog);
                }
            },
            {
                fieldname: 'stock_info',
                label: __('Stock Info'),
                fieldtype: 'HTML',
            }
        ]
    });

    dialog.show();
    get_stock_info(dialog.get_value('item'), dialog.get_value('uom'), dialog);

});

function get_stock_info(item, uom, dialog) {
    frappe.call({
        method: 'ellora.api.get_stock_info',
        args: {
            doctype: cur_frm.doctype,
            name: cur_frm.doc.name,
            item: item,
            uom: uom
        },
        callback: function(r) {
            let html = '';

            if (r.message && r.message.length) {
                html = `
                    <div style="max-height: 400px; overflow-y: auto; overflow-x: auto;">
                        <table class="table table-bordered">
                            <thead>
                                <tr>
                                    <th>${__('Item Code')}</th>
                                    <th>${__('Item Name')}</th>
                                    <th>${__('UOM')}</th>
                                    <th>${__('Warehouse')}</th>
                                    <th>${__('Available Stock')}</th>
                                    <th>${__('Reserved Stock')}</th>
                                </tr>
                            </thead>
                            <tbody>`;

                r.message.forEach(row => {
                    html += `<tr>
                        <td>${row.item_code}</td>
                        <td>${row.item_name}</td>
                        <td>${row.stock_uom}</td>
                        <td>${row.warehouse}</td>
                        <td>${row.actual_qty}</td>
                        <td>${row.reserved_qty}</td>
                    </tr>`;
                });

                html += '</tbody></table></div>';
            } else {
                html = __('No data found');
            }

            dialog.fields_dict.stock_info.$wrapper.html(html);
        }
    });
}





frappe.ui.form.on("Purchase Receipt", {
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

frappe.ui.form.on("Purchase Receipt Item", {
    item_code: function (frm, cdt, cdn) {
        frappe.model.set_value(cdt, cdn, "uom", null);
    }
});