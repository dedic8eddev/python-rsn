var b_datatable = null;

init.push(function () {
    var table_id = 'jq-datatables-example';
    var action_panel_id = 'action-owners';
    var table_columns = [
                { "data" : "checkbox_id", orderable: false },
                { "data" : "img_html" },
                { "data" : "date" },
                { "data" : "author_img_html", orderable: true },

                { "data" : "title", orderable: false },
                { "data" : "description", orderable: false },
                { "data" : "status" },

                { "data" : "domain" },
                { "data" : "designation" },
                { "data" : "grape_variety" },

                { "data" : "region" },
                { "data" : "year" },
                { "data" : "color_text" },

                { "data" : "sparkling_html" },
                { "data" : "place_html", orderable: false },

                { "data" : "comment_number" },
                { "data" : "likevote_number" },
                { "data" : "drank_it_too_number" }
            ];
    var table_default_order = [[ 3, "asc" ]];
    var table_mass_operations = [
        {
            "button_path": ".ui-bootbox-publish",
            "url": url_wineposts_publish_ajax,
            "extra_ser_array": null
        },
        {
            "button_path": ".ui-bootbox-unpublish",
            "url": url_wineposts_unpublish_ajax,
            "extra_ser_array": null
        },
        {
            "button_path": ".ui-bootbox-indoubt",
            "url": url_wineposts_set_in_doubt_ajax,
            "extra_ser_array": null
        },
        {
            "button_path": ".ui-bootbox-bioorg",
            "url": url_wineposts_set_bio_organic_ajax,
            "extra_ser_array": null
        },
        {
            "button_path": ".ui-bootbox-investigate",
            "url": url_wineposts_set_to_investigate,
            "extra_ser_array": null
        },
        {
            "button_path": ".ui-bootbox-undelete",
            "url": url_wineposts_undelete_ajax,
            "extra_ser_array": null
        },
        {
            "button_path": ".ui-bootbox-delete",
            "url": url_wineposts_delete_ajax,
            "extra_ser_array": null,
            "is_confirm": true,
            "confirm_panel_path": ".action_delete_confirm",
            "confirm_button_path": ".ui-bootbox-delete-confirm",
            "cancel_button_path": ".ui-bootbox-delete-cancel"
        },
        {
            "button_path": ".ui-bootbox-refuse",
            "url": url_wineposts_refuse_ajax,
            "extra_ser_array": null,
            "is_confirm": true,
            "confirm_panel_path": ".action_refuse_confirm",
            "confirm_button_path": ".ui-bootbox-refuse-confirm",
            "cancel_button_path": ".ui-bootbox-refuse-cancel"
        }
    ];

    b_datatable = new DataTableFactory(
        table_id,
        'Latest published wineposts: {count}',
        'Latest published wineposts: - {search}: {count}',
        {"count": 0},
        url_winepost_items_ajax,
        table_columns,
        table_default_order,
        table_mass_operations,
        action_panel_id,
        'wineposts'
    );

    b_datatable.draw();
});
