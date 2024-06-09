var init = [];

init.push(function () {
    var $div = $('<div id="signin-demo" class="hidden-xs"><div>PAGE BACKGROUND</div></div>'),
        bgs  = [ ];
    for (var i=0, l=bgs.length; i < l; i++) $div.append($('<img src="' + bgs[i] + '">'));
    $div.find('img').click(function () {
        var img = new Image();
        img.onload = function () {
            $('#page-signin-bg > img').attr('src', img.src);
            $(window).resize();
        }
        img.src = $(this).attr('src');
    });
    $('body').append($div);
});

init.push(function () {
    $("#btn_reset_password").click(function(){

        var serArray = [{
            "name" : "username",
            "value" : $("#p_email_id").val()
        }];

        $.ajax({
                type: "POST",
                dataType: "json",
//                contentType: "json",
                url: reset_password_url,
                data: serArray,
                success: function(data) {
                    $("#renew_modal_label").html(data.label);
                    $("#renew_modal_body").html(data.message);
                    // $("#modal_reset_password").addClass('show in')
                    alert("Password reset e-mail message has been sent. Please follow the further instructions from the message.")
                },
                error: function(data){
                    console.warn(data);
                }
        });
        return false;
    });
});