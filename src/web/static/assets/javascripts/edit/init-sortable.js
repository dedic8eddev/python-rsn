function get_items(){
    var items = $("#current-images-inside").sortable("toArray", {attribute: 'cnt-data-image-file'});
    return items;
}

function get_items_string(){
    var items = $("#current-images-inside").sortable("toArray", {attribute: 'cnt-data-image-file'});

    if (items) {
        return items.join(',');
    }else{
        return '';
    }
}

function get_items_string_old(){
    return $("#id_image_ordering").val();
}


function init_sortable(parent_item_id){
    var b_sortable = null;


    function sortUpdate(event, ui){
        var items = get_items();

        if(parent_item_id){
            var data_out = []
            data_out.push({
                'name': 'parent_item_id',
                'value': parent_item_id
            });

            data_out.push({
                'name': 'ids',
                'value': items.join(',')
            });

            $.ajax({
                type        : "POST",
                url         : url_update_ordering_ajax,
                data        : data_out,
                success: function(data) {

                },
                error: function(data){
                    console.warn(data);
                }
            });

        }else{
            $("#id_image_ordering").val(items.join(','));
        }
    }

    b_sortable = $( "#current-images-inside" ).sortable({
        create: function( event, ui ) {
            var old_val = $("#id_image_ordering").val();
            var items = get_items();

            $("#id_image_ordering").val(get_items_string());
        },

        update: sortUpdate

    });
}
