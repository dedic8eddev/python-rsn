function loadAndInsertHtmlByAjax(url, parentElementId){
    if(url!=undefined && url != null && url != "") {
        $.ajax({
                type: "POST",
                dataType: "html",
                contentType: "text/html",
                url: ajax_related_lists_url,
                data: {},
                success: function(data) {
                    $("#"+parentElementId).html(data);
                },
                error: function(data){
                    console.warn(data);
                }
        });
    }
}

init.push(function () {
    $('#profile-tabs').tabdrop();

    $("#leave-comment-form").expandingInput({
        target: 'textarea',
        hidden_content: '> div',
        placeholder: 'Write message',
        onAfterExpand: function () {
            $('#leave-comment-form textarea').attr('rows', '3').autosize();
        }
    });
})
window.PixelAdmin.start(init);
