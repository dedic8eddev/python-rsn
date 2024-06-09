function update_original_winemaker_name(){
    var id_winemaker = $("#id_winemaker").val();
    var winemaker_name = $("#id_original_winemaker_name").val();

    $.ajax({
        type: "POST",
        dataType: "json",
        url: ajax_update_original_winemaker_name,
        data: {
            "winemaker_id": id_winemaker,
            "winemaker_name": winemaker_name
        },
        success: function(data) {
            if(data.status == 'OK') {
                alert("Winemaker updated OK.");
                hide_original_winemaker();

                select_wm_winepost.select2("destroy");
                $("#id_winemaker").find("option[value="+id_winemaker+"]").html(winemaker_name + " [DRAFT]");
                select_wm_winepost_init();
            }
        },
        error: function(data){
            console.warn(data);
        }
    });
}


function toggle_original_winemaker(){
    $("#original_winemaker_div").collapse("toggle");
}


function show_original_winemaker(){
    $("#original_winemaker_div").collapse("show");
}


function hide_original_winemaker(){
    $("#original_winemaker_div").collapse("hide");
}


init.push(function () {
    if($("#original_winemaker_div").length > 0){
        $("#original_winemaker_div").on("shown.bs.collapse", function() {
            $("#btn_open_edit_winemaker").hide();
            $("#btn_cancel_edit_winemaker").show();
            $("#btn_update_winemaker_name").show();

            $("#id_original_winemaker_open").val(1);
        })
        .on("hidden.bs.collapse", function() {
            $("#btn_open_edit_winemaker").show();
            $("#btn_cancel_edit_winemaker").hide();
            $("#btn_update_winemaker_name").hide();

            $("#id_original_winemaker_open").val(0);
        });

        if($("#id_original_winemaker_open").val()==1){
            show_original_winemaker();
        }
    }
});
