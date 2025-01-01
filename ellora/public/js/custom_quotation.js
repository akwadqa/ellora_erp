frappe.ui.form.on("Quotation Item", "custom_quotation_item_sales_history", function(frm, cdt, cdn) {
    let child_doc = locals[cdt][cdn];
    let item_code = child_doc.item_code;

    const dialog = new frappe.ui.Dialog({
        title: __('Quotation Item Sales History'),
        size: "extra-large",
        fields: [
            {
                fieldname: 'customer',
                label: __('Customer'),
                fieldtype: 'Link',
                options: 'Customer',
                reqd: 0,
                default: cur_frm.doc.party_name,
                change: function() {
                    get_quotation_item_sales_history(dialog.get_value('customer'), dialog.get_value('item'), dialog);
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
                    get_quotation_item_sales_history(dialog.get_value('customer'), dialog.get_value('item'), dialog);
                }
            },
            {
                fieldname: 'items',
                label: __('Items'),
                fieldtype: 'Table',
                fields: [
                    { fieldtype: 'Data', fieldname: 'customer_name', label: __('Customer Name'), in_list_view: 1, read_only: 1, columns: 2 },
                    { fieldtype: 'Link', options: 'Quotation', fieldname: 'quotation', label: __('Quotation'), in_list_view: 1, read_only: 1, columns: 2 },
                    { fieldtype: 'Data', fieldname: 'transaction_date', label: __('Transaction Date'), in_list_view: 1, read_only: 1, columns: 1 },
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
    get_quotation_item_sales_history(dialog.get_value('customer'), dialog.get_value('item'), dialog);
});



function get_quotation_item_sales_history(customer, item, dialog) {
    frappe.call({
        method: 'ellora.api.get_quotation_item_sales_history',
        args: {
            customer: customer,
            item: item
        },
        callback: function(r) {
            if (r.message) {
                // Format the date
                r.message.forEach(row => {
                    row.transaction_date = format_date(row.transaction_date);
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





frappe.ui.form.on("Quotation", {
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

    refresh: function(frm) {
        // Create Delivery Note from Quotation
        if (frm.doc.docstatus === 1 && frappe.model.can_create("Delivery Note")) {
            frm.add_custom_button(
                __("Delivery Note"),
                () => frappe.msgprint("Test"),
                __("Create")
            );
        }

        // // Set query for the UOM field in the items table
        // frm.set_query('uom', 'items', function (doc, cdt, cdn) {
        //     const row = locals[cdt][cdn];
        //     if (!row.item_code) {
        //         // If no item_code is selected, do not apply any filter
        //         return {};
        //     }

        //     // Fetch UOMs from the selected item's UOMs table
        //     frappe.call({
        //         method: "frappe.client.get",
        //         args: {
        //             doctype: "Item",
        //             name: row.item_code,
        //         },
        //         callback: function (r) {
        //             if (r.message) {
        //                 const item = r.message;
        //                 const uom_list = (item.uoms || []).map(uom_entry => uom_entry.uom);
        //                 console.log(uom_list)
        //                 // Dynamically update the query filter for the UOM field
        //                 frm.fields_dict.items.grid.get_field('uom').get_query = function () {
        //                     return {
        //                         filters: {
        //                             name: ["in", uom_list],
        //                         },
        //                     };
        //                 };
        //             }
        //         },
        //     });
        // });
    },

    // custom_make_delivery_note_based_on_delivery_date(frm, for_reserved_stock = false) {
	// 	var delivery_dates = frm.doc.items.map((i) => i.delivery_date);
	// 	delivery_dates = [...new Set(delivery_dates)];

	// 	var item_grid = frm.fields_dict["items"].grid;
	// 	if (!item_grid.get_selected().length && delivery_dates.length > 1) {
	// 		var dialog = new frappe.ui.Dialog({
	// 			title: __("Select Items based on Delivery Date"),
	// 			fields: [{ fieldtype: "HTML", fieldname: "dates_html" }],
	// 		});

	// 		var html = $(`
	// 			<div style="border: 1px solid #d1d8dd">
	// 				<div class="list-item list-item--head">
	// 					<div class="list-item__content list-item__content--flex-2">
	// 						${__("Delivery Date")}
	// 					</div>
	// 				</div>
	// 				${delivery_dates
	// 					.map(
	// 						(date) => `
	// 					<div class="list-item">
	// 						<div class="list-item__content list-item__content--flex-2">
	// 							<label>
	// 							<input type="checkbox" data-date="${date}" checked="checked"/>
	// 							${frappe.datetime.str_to_user(date)}
	// 							</label>
	// 						</div>
	// 					</div>
	// 				`
	// 					)
	// 					.join("")}
	// 			</div>
	// 		`);

	// 		var wrapper = dialog.fields_dict.dates_html.$wrapper;
	// 		wrapper.html(html);

	// 		dialog.set_primary_action(__("Select"), function () {
	// 			var dates = wrapper
	// 				.find("input[type=checkbox]:checked")
	// 				.map((i, el) => $(el).attr("data-date"))
	// 				.toArray();

	// 			if (!dates) return;

	// 			frm.events.custom_make_delivery_note(frm, dates, for_reserved_stock);
	// 			dialog.hide();
	// 		});
	// 		dialog.show();
	// 	} else {
	// 		frm.events.custom_make_delivery_note([], for_reserved_stock);
	// 	}
	// },

	// custom_make_delivery_note(frm, delivery_dates, for_reserved_stock = false) {
	// 	frappe.model.open_mapped_doc({
	// 		method: "ellora.api.make_delivery_note",
	// 		args: {
    //             source_name: frm.doc.name,
	// 			delivery_dates,
	// 			for_reserved_stock: for_reserved_stock,
	// 		},
	// 		freeze: true,
	// 		freeze_message: __("Creating Delivery Note ..."),
	// 	});
	// }

});