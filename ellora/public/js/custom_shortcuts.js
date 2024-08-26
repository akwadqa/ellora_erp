frappe.ui.keys.add_shortcut({
    description: __('Stock Monitor'),
    shortcut: 'shift+ctrl+f',
    action: function() {
        // if (cur_frm.doctype === 'Sales Invoice' && cur_frm.doc.items && cur_frm.doc.items.length > 0) {
        stock_monitor_dialog();
        // }
    },
    ignore_inputs: true
});

function stock_monitor_dialog() {
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
                change: function() {
                    get_stock_info(dialog.get_value('item'), dialog);
                }
            },
            {
                fieldname: 'stock_info',
                label: __('Stock Info'),
                fieldtype: 'HTML',
            }
        ],
    });

    dialog.show();
    get_stock_info(dialog.get_value('item'), dialog);
}

function get_stock_info(item, dialog) {
    const args = {
        item: item
    };

    if (cur_frm && cur_frm.doctype === 'Sales Invoice') {
        args.sales_invoice = cur_frm.doc.name;
    }

    frappe.call({
        method: 'ellora.api.get_stock_info',
        args: args,
        callback: function(r) {
            let html = '';

            if (r.message && r.message.length) {
                html = `
                    <div style="max-height: 400px; overflow-y: auto; overflow-x: auto;">
                        <table class="table table-bordered">
                            <thead>
                                <tr>
                                    <th style="white-space: nowrap;">${__('Item Code')}</th>
                                    <th style="white-space: nowrap;">${__('Item Name')}</th>
                                    <th style="white-space: nowrap;">${__('UOM')}</th>
                                    <th style="white-space: nowrap;">${__('Warehouse')}</th>
                                    <th style="white-space: nowrap;">${__('Available Stock')}</th>
                                    <th style="white-space: nowrap;">${__('Reserved Stock')}</th>
                                </tr>
                            </thead>
                            <tbody>`;

                r.message.forEach(row => {
                    html += `<tr>
                        <td style="white-space: nowrap;">${row.item_code}</td>
                        <td style="white-space: nowrap;">${row.item_name}</td>
                        <td style="white-space: nowrap;">${row.stock_uom}</td>
                        <td style="white-space: nowrap;">${row.warehouse}</td>
                        <td style="white-space: nowrap;">${row.actual_qty}</td>
                        <td style="white-space: nowrap;">${row.reserved_qty}</td>
                    </tr>`;
                });

                html += '</tbody></table></div>';
            }

            dialog.fields_dict.stock_info.$wrapper.html(html);
        }
    });
}


frappe.ui.keys.add_shortcut({
    description: __('Item Sales History'),
    shortcut: 'shift+ctrl+h',
    action: function() {
        if (cur_frm && cur_frm.doctype === 'Sales Invoice') {
            item_sales_history_dialog();
        }
    },
    ignore_inputs: true
});

function item_sales_history_dialog() {
    const dialog = new frappe.ui.Dialog({
        title: __('Item Sales History'),
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
                    get_item_sales_history(dialog.get_value('customer'), dialog.get_value('item'), dialog);
                }
            },
            {
                fieldname: 'item',
                label: __('Item'),
                fieldtype: 'Link',
                options: 'Item',
                reqd: 0,
                change: function() {
                    get_item_sales_history(dialog.get_value('customer'), dialog.get_value('item'), dialog);
                }
            },
            {
                fieldname: 'items',
                label: __('Items'),
                fieldtype: 'Table',
                fields: [
                    { fieldtype: 'Data', fieldname: 'customer_name', label: __('Customer Name'), in_list_view: 1, read_only: 1, columns: 2 },
                    { fieldtype: 'Link', options: 'Sales Invoice', fieldname: 'sales_invoice', label: __('Sales Invoice'), in_list_view: 1, read_only: 1, columns: 2 },
                    { fieldtype: 'Data', fieldname: 'posting_date', label: __('Posting Date'), in_list_view: 1, read_only: 1, columns: 1 },
                    { fieldtype: 'Link', options: 'Item', fieldname: 'item_code', label: __('Item Code'), in_list_view: 1, read_only: 1, columns: 3 },
                    { fieldtype: 'Data', fieldname: 'qty', label: __('Quantity'), in_list_view: 1, read_only: 1, columns: 1 },
                    { fieldtype: 'Currency', fieldname: 'rate', label: __('Rate'), in_list_view: 1, read_only: 1, columns: 1 }
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
    get_item_sales_history(dialog.get_value('customer'), dialog.get_value('item'), dialog);
}

function get_item_sales_history(customer, item, dialog) {
    frappe.call({
        method: 'ellora.api.get_item_sales_history',
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