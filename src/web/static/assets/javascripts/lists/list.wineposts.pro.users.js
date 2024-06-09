init.push(function () {
    var action_panel_id_users = 'action-users';
    var table_id_users = 'jq-datatables-wine-posts-users';
    var searchId = 'jq-datatables-wine-posts-users-search';
    var table_columns_users = [
                { "data" : "checkbox_id", orderable: false },
                { "data" : "status_html"},
                { "data" : "img_html" },
                { "data" : "label_html", orderable: false },
                { "data" : "matched_html", className: 'col-matched' },

                { "data" : "winemaker_name" },
                { "data" : "domain" },
                { "data" : "designation" },
                { "data" : "grape_variety" },
                { "data" : "region" },

                { "data" : "year" },
                { "data" : "color_text" },
                { "data" : "sparkling_html" },
                { "data" : "description", orderable: false },
                { "data" : "date" },

                { "data" : "author_img_html", orderable: true },
                { "data" : "expert_img_html", orderable: true },
                { "data" : "geolocation", orderable: true },

                { "data" : "comment_number" },
                { "data" : "price" },
//                { "data" : "likevote_number" },
//                { "data" : "drank_it_too_number" }
            ];
    var table_default_order_users = [[ 14, "desc" ]];
    var table_mass_operations_users = [
        {
            "button_path": ".ui-bootbox-publish",
            "url": url_wineposts_publish_ajax,
            "extra_ser_array": null,
            "is_confirm": true,
            "confirm_panel_path": ".action_change_status_confirm",
            "confirm_button_path": ".ui-bootbox-change-status-confirm",
            "cancel_button_path": ".ui-bootbox-change-status-cancel"
        },
        {
            "button_path": ".ui-bootbox-unpublish",
            "url": url_wineposts_unpublish_ajax,
            "extra_ser_array": null,
            "is_confirm": true,
            "confirm_panel_path": ".action_change_status_confirm",
            "confirm_button_path": ".ui-bootbox-change-status-confirm",
            "cancel_button_path": ".ui-bootbox-change-status-cancel"
        },
        {
            "button_path": ".ui-bootbox-indoubt",
            "url": url_wineposts_set_in_doubt_ajax,
            "extra_ser_array": null,
            "is_confirm": true,
            "confirm_panel_path": ".action_change_status_confirm",
            "confirm_button_path": ".ui-bootbox-change-status-confirm",
            "cancel_button_path": ".ui-bootbox-change-status-cancel"
        },
        {
            "button_path": ".ui-bootbox-bioorg",
            "url": url_wineposts_set_bio_organic_ajax,
            "extra_ser_array": null,
            "is_confirm": true,
            "confirm_panel_path": ".action_change_status_confirm",
            "confirm_button_path": ".ui-bootbox-change-status-confirm",
            "cancel_button_path": ".ui-bootbox-change-status-cancel"
        },
        {
            "button_path": ".ui-bootbox-investigate",
            "url": url_wineposts_set_to_investigate,
            "extra_ser_array": null,
            "is_confirm": true,
            "confirm_panel_path": ".action_change_status_confirm",
            "confirm_button_path": ".ui-bootbox-change-status-confirm",
            "cancel_button_path": ".ui-bootbox-change-status-cancel"
        },
        {
            "button_path": ".ui-bootbox-undelete",
            "url": url_wineposts_undelete_ajax,
            "extra_ser_array": null,
            "is_confirm": true,
            "confirm_panel_path": ".action_change_status_confirm",
            "confirm_button_path": ".ui-bootbox-change-status-confirm",
            "cancel_button_path": ".ui-bootbox-change-status-cancel"
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
        },
        {
            "button_path": ".ui-bootbox-mop-not-wine",
            "url": url_mop_move_to_general_post,
            "extra_ser_array": null,
            "is_confirm": true,
            "confirm_panel_path": ".action_change_status_confirm",
            "confirm_button_path": ".ui-bootbox-change-status-confirm",
            "cancel_button_path": ".ui-bootbox-change-status-cancel"
        }
    ];

    var b_datatable_users = new DataTableFactory(
        table_id_users,
        'Latest published wineposts from users: {count}',
        'Latest published wineposts from users - {search}: {count}',
        {"count": 0},
        url_winepost_items_users_ajax,
        table_columns_users,
        table_default_order_users,
        table_mass_operations_users,
        action_panel_id_users,
        'wineposts'
    );

    b_datatable_users.draw();
});

init.push(function() {
    $('a[data-toggle="tab"]').on('shown.bs.tab', function (e) {
      var target = $(e.target).attr("href"); // activated tab
      if (target == '#all') {
        $('#jq-datatables-wine-posts-all img:visible').unveil();
      } else if (target == '#users') {
        $('#jq-datatables-wine-posts-users img:visible').unveil();
      } else if (target == '#owners') {
        $('#jq-datatables-wine-posts-owners img:visible').unveil();
      } else if (target == '#geolocated') {
        $('#jq-datatables-wine-posts-geolocated img:visible').unveil();
      }
    });
});
