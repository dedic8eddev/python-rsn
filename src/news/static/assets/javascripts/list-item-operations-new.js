function handleActionFooter(){
    if($('[name="ids"]:checked').length > 0){
        $(".action_item_number").html("" + $('[name="ids"]:checked').length);
        $(".action-confirm").hide();

        $("#action").show();
        $(".action-main").show();

        if(localStorage.getItem("activeTab")=="venues"){
            $("#ui-bootbox-ban-user").prop('disabled', true);
            $("#ui-bootbox-unban-user").prop('disabled', true);
        }

    }else{
        $("#action").hide();
        $('[name="check-all"]').prop('checked', false);
    }
}

$('a[data-toggle="tab"]').on('shown.bs.tab', function (e) {
    $('[name="ids"]').prop("checked",false);    
    $('[name="check-all"]').prop("checked",false);
    $("#action").hide();
})

function setHandleActionFooterTable(table_id, toggle_all_id, actionPanelId) {
    $('#'+table_id+' [name="ids"]').unbind('click');

    $('#'+table_id+' [name="ids"]').click(function() {
        handleActionFooterTable(table_id, toggle_all_id, actionPanelId);
    });
}

function setHandleActionFooterTableToggleAll(toggle_all_id, table_id, toggle_all_id, actionPanelId) {
    $('#'+toggle_all_id).unbind('click');

    $('#'+toggle_all_id).click(function() {
        $('.table-bordered input[type="checkbox"]').prop('checked', $(this).prop('checked'));
        handleActionFooterTable(table_id, toggle_all_id, actionPanelId);
    });
}

function handleActionFooterTable(table_id, toggle_all_id, actionPanelId){
    if($('#'+table_id+ ' [name="ids"]:checked').length > 0){
        $("#"+actionPanelId + "  .action_item_number").html("" + $('#'+table_id+ ' [name="ids"]:checked').length);
        $("#"+actionPanelId + "  .action-confirm").hide();

        $("#"+actionPanelId).show();
        $("#"+actionPanelId + "  .action-main").show();

    }else{
        $("#"+actionPanelId).hide();
        $("#"+toggle_all_id).prop('checked', false);
    }
}


function cancelSelection() {
    cancelSelectionPanel("action");
    uncheckListItems();
    $("#action").hide();
}

function cancelSelectionActionPanelId(actionPanelId) {
    cancelSelectionPanel(actionPanelId);
    uncheckListItems();
    $("#"+actionPanelId).hide();
}

function cancelSelectionPanel(panelId) {
    $("#"+panelId).hide();
}

function uncheckListItems(){
    $("input[name=check-all]").prop('checked', false);
    if($('[name="ids"]:checked').length > 0){
        $('[name="ids"]:checked').prop('checked', false);
    }

}

function bindSingleOperationConfirm(idRule, urlConfirmed, actionPanelId, confirmButtonId, cancelButtonId, entities, extraCallback, tableName, toggleAllId, isPipeline){
    var idStartIndex = idRule.length;
    $('[id^="'+idRule+'"]').unbind('click');
    $('[id^="'+idRule+'"]').click(function(){
        var id = $(this).attr('id').substr(idRule.length);

        singleOperationConfirm(id, urlConfirmed, actionPanelId, confirmButtonId, cancelButtonId, entities, extraCallback, tableName, toggleAllId, isPipeline);
        return false;
    });
}

function singleOperationConfirm(id, url, actionPanelId, confirmButtonId, cancelButtonId, entities, extraCallback, tableName, toggleAllId, isPipeline){
    $("#"+actionPanelId).show();
    $('.table-bordered input[type="checkbox"]:enabled').prop('checked', false);

    $("#"+confirmButtonId).unbind('click');
    $("#"+confirmButtonId).click(function(){
        singleOperation(id, actionPanelId, url, entities, extraCallback, tableName, toggleAllId, isPipeline);
        return false;
    });

    $("#"+cancelButtonId).click(function(){
        cancelSelectionPanel(actionPanelId);
        return false;
    });

}

function singleOperation(id, actionPanelId, url, entities, extraCallback, tableName, toggleAllId, isPipeline){
    var serArray = [{
        "name" : "ids",
        "value" : id
    }]
    $.ajax({
        type: "POST",
        url: url,
        data: serArray,
        success: function(data) {
            if (tableName != undefined && tableName != null && tableName != '') {
                // pass
            } else {
                tableName = '#jq-datatables-example';
            }

            if(isPipeline)  {
                $(tableName).DataTable().clearPipeline().draw();
            }  else {
                $(tableName).DataTable().ajax.reload();
            }

            if(toggleAllId != undefined && toggleAllId != null && toggleAllId != '') {
                $("#" + toggleAllId).prop('checked', false);
            } else {
                $("#toggle-all").prop('checked', false);
            }
            $("#"+actionPanelId).hide();
            if (entities != undefined && entities != null && $("#menu_num_"+entities).length > 0 &&
                data['count']!=undefined && data['count']!=null && data['count']!=''){
                $("#menu_num_"+entities).html(data['count']);
            }
            if((extraCallback != undefined) && (extraCallback != null)){
                extraCallback();
            }
            return false;
        },
        error: function(data){
            console.warn(data);
            return false;
        }
    });

}

var mass_operation_table_id = 'dataTable';

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      var cookies = document.cookie.split(';');
      for (var i = 0; i < cookies.length; i++) {
        var cookie = cookies[i].trim();
          if (cookie.substring(0, name.length + 1) === (name + '=')) {
            cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
            break;
          }
      }
    }
    return cookieValue;
}

function massOperationCommon(url, entities, clear_function, extraSerArray){
    var serArray = $('input[name^="ids"][type="checkbox"]:checked').serializeArray();
    if (extraSerArray != undefined && Array.isArray(extraSerArray) && extraSerArray.length > 0) {
        serArray = serArray.concat(extraSerArray);
    }
    // $.ajax({
    //     type: "POST",
    //     url: url,
    //     data: serArray,
    //     success: function(data) {
    //         clear_function();
    //         $("#toggle-all").prop('checked', false);
    //         $(".action-confirm").hide();
    //         $("#action").hide();
    //         if (entities != undefined && entities != null && $("#menu_num_"+entities).length > 0 &&
    //             data['count']!=undefined && data['count']!=null && data['count']!=''){
    //             $("#menu_num_"+entities).html(data['count']);
    //         }
    //     },
    //     error: function(data){
    //         console.warn(data);
    //     }
    // });


    formData = new FormData(),
        xhr = new XMLHttpRequest();

        for(var i = 0; i < serArray.length; i++){
            console.log(serArray[i].name,serArray[i].value)
            formData.append(serArray[i].name,serArray[i].value);
        } 
        xhr.open('POST', url, true);
        xhr.onload = function () {
            if (xhr.status === 200) {
                clear_function();
                $("#toggle-all").prop('checked', false);
                $(".action-confirm").hide();
                $("#action").hide();
                if (entities != undefined && entities != null && $("#menu_num_"+entities).length > 0 &&
                    data['count']!=undefined && data['count']!=null && data['count']!=''){
                    $("#menu_num_"+entities).html(data['count']);
                }
            }else{
                console.log(`Error ${xhr.status}: ${xhr.statusText}`)
            }
        };
        xhr.send(formData); 
}

function massOperationCommonBanUnban(url, entities, clear_function, extraSerArray,action){   
    let serArray = $('input[name^="ids"][type="checkbox"]:checked').map(function() {
        let o = this;
        return Object.keys(o.dataset).reduce(function(c, v) { c[v] = o.dataset[v]; return c;}, {})
    }).get();

    for(var i = 0; i < serArray.length; i++){
        if(action == 'ban' && serArray[i].status != 25 || action == 'unban' && serArray[i].status == 25){
            formData = new FormData(),
            xhr = new XMLHttpRequest();
            for(var i = 0; i < serArray.length; i++){
                formData.append("ids",serArray[i].authorid);
            } 
            xhr.open('POST', url, true);
            xhr.onload = function () {
                if (xhr.status === 200) {
                    clear_function();
                    $("#toggle-all").prop('checked', false);
                    $(".action-confirm").hide();
                    $("#action").hide();
                    if (entities != undefined && entities != null && $("#menu_num_"+entities).length > 0 &&
                        data['count']!=undefined && data['count']!=null && data['count']!=''){
                        $("#menu_num_"+entities).html(data['count']);
                    }
                }else{
                    console.log(`Error ${xhr.status}: ${xhr.statusText}`)
                }
            };
            xhr.send(formData); 
        }
        else if(action == 'ban' && serArray[i].status == 25){
            alert(serArray[i].author + " is already banned")
        }
        else if(action == 'unban' && serArray[i].status != 25){
            alert(serArray[i].author + " is not ban")
        }
    }

}

function massOperationCommonDelete(url, entities, clear_function, extraSerArray){
    var serArray = $('input[name^="ids"][type="checkbox"]:checked').serializeArray();
    if (extraSerArray != undefined && Array.isArray(extraSerArray) && extraSerArray.length > 0) {
        serArray = serArray.concat(extraSerArray);
    }
    var csrftoken = getCookie('csrftoken');
    if(serArray.length >= 1) {
        for(i = 0; i <= serArray.length; i++){
            $.ajax({
                type: "DELETE",
                url: url+serArray[i].value,
                beforeSend: function(xhr, settings) {
                    xhr.setRequestHeader("X-CSRFToken", csrftoken);
                },
                success: function(data) {
                    clear_function();
                    $("#toggle-all").prop('checked', false);
                    $(".action-confirm").hide();
                    $("#action").hide();
                    if (entities != undefined && entities != null && $("#menu_num_"+entities).length > 0 &&
                        data['count']!=undefined && data['count']!=null && data['count']!=''){
                        $("#menu_num_"+entities).html(data['count']);
                    }
                    $(".all_count").html(parseInt(localStorage.getItem("reviews-count")) + parseInt(localStorage.getItem("comments-count")) + parseInt(localStorage.getItem("events-count")) + parseInt(localStorage.getItem("pictures-count")))
                },
                error: function(data){
                    console.warn(data);
                }
            });
        }
    }
}

function massOperationPipeline(url, entities, extraSerArray){
    massOperationCommon(
        url,
        entities,
        $("." + mass_operation_table_id).DataTable().clearPipeline().draw,
        extraSerArray
    );
}

function massOperationPipelineBanUnban(url, entities, extraSerArray,action){
    massOperationCommonBanUnban(
        url,
        entities,
        $("." + mass_operation_table_id).DataTable().clearPipeline().draw,
        extraSerArray,
        action
    );
}

function massOperationPipelineDelete(url, entities, extraSerArray){
    massOperationCommonDelete(
        url,
        entities,
        $("." + mass_operation_table_id).DataTable().clearPipeline().draw,
        extraSerArray
    );
}

function massOperationPipelineTable(url, entities, table_id, extraSerArray){
    massOperationCommon(
        url,
        entities,
        $("#" + table_id).DataTable().clearPipeline().draw,
        extraSerArray
    );
}

function massOperation(url, entities, extraSerArray){
    massOperationCommon(
        url,
        entities,
        $("." + mass_operation_table_id).DataTable().ajax.reload,
        extraSerArray
    );
}

function massOperationConfirm(url, confirmPanelId, confirmButtonId, cancelButtonId, entities){
    $(".action-main").hide();
    $("#"+confirmPanelId).show();
    $("#"+confirmButtonId).unbind("click");
    $("#"+cancelButtonId).unbind("click");

    $("#"+confirmButtonId).click(function(){
        massOperation(url, entities);
        return false;
    });


    $("#"+cancelButtonId).click(function(){
        $(".action-confirm").hide();
        $(".action-main").show();
        return false;
    });
}

function massOperationTable(url, entities, mass_operation_table_id, extraSerArray){
    massOperationCommon(
        url,
        entities,
        $("." + mass_operation_table_id).DataTable().ajax.reload,
        extraSerArray
    );
}

function massOperationConfirmTable(url, mass_operation_table_id, confirmPanelId, confirmButtonId, cancelButtonId, entities){
    $(".action-main").hide();
    $("#"+confirmPanelId).show();

    $("#"+confirmButtonId).unbind("click");
    $("#"+cancelButtonId).unbind("click");


    $("#"+confirmButtonId).click(function(){
        massOperationTable(url, entities, mass_operation_table_id);
        return false;
    });

    $("#"+cancelButtonId).click(function(){
        $(".action-confirm").hide();
        $(".action-main").show();
        return false;
    });
}

function massOperationConfirmPipeline(url, confirmPanelId, confirmButtonId, cancelButtonId, entities){
    $("#"+confirmButtonId).prop('disabled', false);
    $(".action-main").hide();
    $("#"+confirmPanelId).show();

    $("#"+confirmButtonId).unbind("click");
    $("#"+cancelButtonId).unbind("click");

    $("#"+confirmButtonId).click(function(){
        $("#"+confirmButtonId).prop('disabled', true);
        massOperationPipeline(url, entities);
        return false;
    });

    $("#"+cancelButtonId).click(function(){
        $(".action-confirm").hide();
        $(".action-main").show();
        return false;
    });
}

function massOperationConfirmPipelineBanUnban(url, confirmPanelId, confirmButtonId, cancelButtonId, entities,action){
    $("#"+confirmButtonId).prop('disabled', false);
    $(".action-main").hide();
    $("#"+confirmPanelId).show();

    $("#"+confirmButtonId).unbind("click");
    $("#"+cancelButtonId).unbind("click");

    $("#"+confirmButtonId).click(function(){
        $("#"+confirmButtonId).prop('disabled', true);
        massOperationPipelineBanUnban(url, entities,'',action);
        return false;
    });

    $("#"+cancelButtonId).click(function(){
        $(".action-confirm").hide();
        $(".action-main").show();
        return false;
    });
}

function massOperationConfirmPipelineDelete(url, confirmPanelId, confirmButtonId, cancelButtonId, entities){
    $("#"+confirmButtonId).prop('disabled', false);
    $(".action-main").hide();
    $("#"+confirmPanelId).show();

    $("#"+confirmButtonId).unbind("click");
    $("#"+cancelButtonId).unbind("click");

    $("#"+confirmButtonId).click(function(){
        $("#"+confirmButtonId).prop('disabled', true);
        massOperationPipelineDelete(url, entities);
        return false;
    });

    $("#"+cancelButtonId).click(function(){
        $(".action-confirm").hide();
        $(".action-main").show();
        return false;
    });
}

function massOperationConfirmPipelineTable(url, table_id, confirmPanelId, confirmButtonId, cancelButtonId, entities){
    $(".action-main").hide();
    $("#"+confirmPanelId).show();
    $("#"+confirmButtonId).click(function(){
        massOperationPipelineTable(url, entities, table_id);
        return false;
    });

    $("#"+cancelButtonId).click(function(){
        $(".action-confirm").hide();
        $(".action-main").show();
        return false;
    });
}
