init.push(function () {
    $('#jq-datatables-referee').dataTable({
        ajax: {
            "url": url_get_winepost_referee_items,
            "type" : "POST",
            //"data": function (d) {
            //    d.extra_search = $('#extra').val();
            //}
        },
        "aLengthMenu": [ 100, 500, 1000 ],
        columns: [
            { "data" : "checkbox_id", orderable: false },
            { "data" : "author_img_html" },
            { "data" : "img_html" },
            { "data" : "title" },

            { "data" : "description" },
            { "data" : "status_html" },
            { "data" : "winemaker_name" },
            { "data" : "domain" },

            { "data" : "designation" },
            { "data" : "grape_variety" },
            { "data" : "region" },
            { "data" : "year" },

            { "data" : "color_text" },
            { "data" : "sparkling_html" },
            { "data" : "place_html" },

            { "data" : "comment_number" },
            { "data" : "likevote_number" },
            { "data" : "drank_it_too_number" },
        ],
        drawCallback: function(settings) {
            $('[data-toggle="tooltip"]').tooltip();

            $('[name="ids"]').click(function() {
                //handleActionFooter();
            });
            if((settings.aoData != undefined)&&(settings.aoData != null)&&(settings.aoData.length >0)){
                $('#jq-datatables-reviews_wrapper .table-caption').text(settings.aoData.length + ' other reviews');
            }else{
                $('#jq-datatables-reviews_wrapper .table-caption').text('No other reviews found.');
            }

            $('#jq-datatables-reviews_wrapper .dataTables_filter input').attr('placeholder', 'Search...');

            $('#toggle-all').click(function() {
                $('#jq-datatables-reviews .table-bordered input[type="checkbox"]').prop('checked', $(this).prop('checked'));
                // handleActionFooter();
            });

        }
    });
});

init.push(function () {
    $("#id_is_parent_post").unbind('click');
    $("#define_as_child").unbind('click');

    $("#id_is_parent_post").click(function(){
        var is_checked = $(this).prop('checked');

        if(is_checked){
//            if(wm_natural) {
            if(sel_display_natural) {
                pdg_widget.set_current_value(20);
                pdg_widget.refresh();
            }

            $('#jq-datatables-referee').DataTable().ajax.reload(function (json) {
                if((json.data != undefined) && (json.data.length > 0)){
                    $("#actionpost").show();
                }
            });
        }else{
            $("#actionpost").hide();
        }
    });

    $("#define_as_child").click(function(){
        var is_checked = $(this).prop('checked');

        if(is_checked){
            $("#actionpostparent").show();
        }else{
            $("#actionpostparent").hide();
        }
    });

    $("#ui-bootbox-referee-post-cancel").click(function(){
        $("#id_is_parent_post").prop('checked', false);
        $("#actionpost").hide();
    });

    $("#ui-bootbox-referee-post-confirm").click(function(){
        $("#actionpost").hide();
        return true;
    });


});
