if(!is_new) {
    init.push(function () {
        var action_panel_id_users = 'action-users';
        var table_id_users = 'jq-datatables-posts';

        if (user_is_admin) {
            var table_columns_users = [
                { "data" : "checkbox_id", orderable: false },
                { "data" : "img_html", orderable: false  },
                { "data" : "date" },

                { "data" : "title" },
                { "data" : "description", orderable: false },
                { "data" : "status_html"},

                { "data" : "designation" },
                { "data" : "grape_variety" },
                { "data" : "winemaker" },
                { "data" : "year" },

                { "data" : "color_text" },
                { "data" : "sparkling_html" },

                { "data" : "comment_number" },
                { "data" : "likevote_number" },
                { "data" : "drank_it_too_number" }
            ];
        } else {
            var table_columns_users = [
                { "data" : "checkbox_id", orderable: false },
                { "data" : "img_html", orderable: false  },
                { "data" : "date" },

                { "data" : "title" },
                { "data" : "description", orderable: false },
                { "data" : "status_html"},

                { "data" : "designation" },
                { "data" : "grape_variety" },
                { "data" : "year" },

                { "data" : "color_text" },
                { "data" : "sparkling_html" },

                { "data" : "comment_number" },
                { "data" : "likevote_number" },
                { "data" : "drank_it_too_number" }
            ];
        }

        var table_default_order_users = [[ 2, "desc" ]];
        var table_mass_operations_users = [
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

        var b_datatable_users = new DataTableFactory(
            table_id_users,
            'Posts reviewed : {count}',
            'Posts reviewed - {search} : {count}',
            {"count": 0},
            url_userpost_items_ajax,
            table_columns_users,
            table_default_order_users,
            table_mass_operations_users,
            action_panel_id_users,
            'wineposts'
        );

        b_datatable_users.draw();
    });

}
