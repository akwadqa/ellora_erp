frappe.ui.form.on("Delivery Note Item", "custom_stock_info", function(frm, cdt, cdn) {
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


frappe.ui.form.on("Delivery Note Item", "custom_delivery_note_item_sales_history", function(frm, cdt, cdn) {
    let child_doc = locals[cdt][cdn];
    let item_code = child_doc.item_code;

    const dialog = new frappe.ui.Dialog({
        title: __('Delivery Note Item Sales History'),
        size: "extra-large",
        fields: [
            {
                fieldname: 'customer',
                label: __('Customer'),
                fieldtype: 'Link',
                options: 'Customer',
                reqd: 0,
                default: cur_frm.doc.customer,
                change: function() {
                    get_delivery_note_item_sales_history(dialog.get_value('customer'), dialog.get_value('item'), dialog);
                }
            },
            {
                fieldname: 'item',
                label: __('Item'),
                fieldtype: 'Link',
                options: 'Item',
                reqd: 0,
                default: item_code,
                change: function() {
                    get_delivery_note_item_sales_history(dialog.get_value('customer'), dialog.get_value('item'), dialog);
                }
            },
            {
                fieldname: 'items',
                label: __('Items'),
                fieldtype: 'Table',
                fields: [
                    { fieldtype: 'Data', fieldname: 'customer_name', label: __('Customer Name'), in_list_view: 1, read_only: 1, columns: 2 },
                    { fieldtype: 'Link', options: 'Delivery Note', fieldname: 'delivery_note', label: __('Delivery Note'), in_list_view: 1, read_only: 1, columns: 2 },
                    { fieldtype: 'Data', fieldname: 'posting_date', label: __('Posting Date'), in_list_view: 1, read_only: 1, columns: 1 },
                    { fieldtype: 'Link', options: 'Item', fieldname: 'item_code', label: __('Item Code'), in_list_view: 1, read_only: 1, columns: 2 },
                    { fieldtype: 'Data', fieldname: 'qty', label: __('Quantity'), in_list_view: 1, read_only: 1, columns: 1 },
                    { fieldtype: 'Currency', fieldname: 'rate', label: __('Rate'), in_list_view: 1, read_only: 1, columns: 1 },
                    { fieldtype: 'Link', options: 'UOM', fieldname: 'uom', label: __('UOM'), in_list_view: 1, read_only: 1, columns: 1 }
                ],
                data: [],
                get_data: function() {
                    return [];
                }
            }
        ],
        primary_action_label: __('Update Rate'),
        primary_action: function() {
            const selected_items = dialog.fields_dict.items.grid.get_selected_children();
            if (selected_items.length > 0) {
                update_item_rate(selected_items);
                dialog.hide();
            } else {
                frappe.msgprint(__('Please select an item to update the rate'));
            }
        }
    });

    dialog.show();
    get_delivery_note_item_sales_history(dialog.get_value('customer'), dialog.get_value('item'), dialog);
});



function get_delivery_note_item_sales_history(customer, item, dialog) {
    frappe.call({
        method: 'ellora.api.get_delivery_note_item_sales_history',
        args: {
            customer: customer,
            item: item
        },
        callback: function(r) {
            if (r.message) {
                // Format the date
                r.message.forEach(row => {
                    row.posting_date = format_date(row.posting_date);
                });
                const table_field = dialog.fields_dict.items;
                table_field.grid.df.data = r.message;
                table_field.grid.refresh();
            }
        }
    });
}

function update_item_rate(selected_items) {
    const items = cur_frm.doc.items;
    let updated = false;
    selected_items.forEach(selected_item => {
        const item_code = selected_item.item_code;
        const rate = selected_item.rate;
        for (const child of items) {
            if (child.item_code === item_code) {
                frappe.model.set_value(child.doctype, child.name, 'rate', rate);
                updated = true;
            }
        }
    });
    if (updated) {
        cur_frm.refresh_field('items');
        cur_frm.save();
    }
}

// Format date to yy-mm-dd
function format_date(date_string) {
    const date = new Date(date_string);
    const year = date.getFullYear().toString().slice(-2);
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const day = date.getDate().toString().padStart(2, '0');
    return `${year}-${month}-${day}`;
}





frappe.ui.form.on("Delivery Note", {
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

    onload_post_render: function(frm) {
        frm.set_query("item_code", "items", function () {
            return {
                query: "erpnext.controllers.queries.item_query",
                filters: { is_sales_item: 1, customer: frm.doc.customer, has_variants: 0, warehouse: frm.doc.set_warehouse},
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

frappe.ui.form.on("Delivery Note Item", {
    item_code: function (frm, cdt, cdn) {
        frappe.model.set_value(cdt, cdn, "uom", null);
    }
});