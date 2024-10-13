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