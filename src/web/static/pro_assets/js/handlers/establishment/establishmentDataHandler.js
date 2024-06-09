function get_establishment_data(url) {
    $.ajax({
        url: url,
        method: "GET",
        success: function (data) {
            if (Object.entries(data).length !== 0) render_establishment_data(data);
            else $(".custom-preloader").fadeOut('slow')
        },
        error: function (xhr, status, error) {
            console.log(error);
        }
    })
}


function render_establishment_data(establishment) {
    let imgScr = establishment.ref_image_id;
    let teamImage = establishment.team_image;

    $("#tinymce")[0].innerHTML = establishment.description;
    $("#input-file-now-custom-1").attr("data-default-file", imgScr);
    $("#input-file-now-custom-2").attr("data-default-file", teamImage);
    $("#name").attr("value", establishment.name);
    $("#input-6").attr("value", establishment.email);
    $("#input-7").attr("value", establishment.website_url);
    $("#facebook").attr("value", establishment.social_facebook_url);
    $("#twitter").attr("value", establishment.social_twitter_url);
    $("#instagram").attr("value", establishment.social_instagram_url);
    $("#book_table").attr("value", establishment.formitable_url);
    $("#latitude").attr("value", establishment.latitude);
    $("#longitude").attr("value", establishment.longitude);
    $("#pin_latitude").attr("value", establishment.pin_latitude);
    $("#pin_longitude").attr("value", establishment.pin_longitude);


    toggle_checkboxes(establishment.types);

    $("#address").attr("value", establishment.address);
    $("#city").attr("value", establishment.city);

    replace_select_data("country", establishment.country);
    replace_select_data("state", establishment.state);

    $("#zip").attr("value", establishment.zip_code);
    $("#phone").attr("value", establishment.phone_number);
    initialize_dropify(imgScr, teamImage);
}

// Replaces value of dropdown selector
function replace_select_data(selectId, replaceString) {
    let selectElement = $("#" + selectId);

    selectElement.children().eq(0).removeAttr('selected');
    selectElement.attr("value", replaceString);
    selectElement.append("<option selected>" + replaceString + "</option>");
}

function initialize_dropify() {
    let logoDropifyElement = $("#input-file-now-custom-1");
    let teamDropifyElement = $("#input-file-now-custom-2");
    // let message = language === "FR" ? 'Glisser/déposer<br>un fichier ou cliquer' : 'Drag and drop a file here or click';
    let message;
    if(language === "FR"){
        message = 'Glisser/déposer<br>un fichier ou cliquer';
    }else if(language === "EN"){
        message = 'Drag and drop a file here or click';
    }else if(language === "IT"){
        message = 'Trascina e rilascia un file o fai clic su';
    }else{
        message = 'Drag and drop a file here or click';
    }
    // let style = language === "FR" ? 'transform: translateY(25%)!important;' : '';

    logoDropifyElement.dropify({
        tpl: {
            clearButton: '<button type="button" class="btn btn-square btn-danger btn-delete dropify-clear" id="delete-logo"><i class="fa fa-trash-o"></i></button>',
            message: '<div class="dropify-message"><span class="file-icon" /> <p>' + message + '</p></div>', // style="' + style + '
        },
    });

    teamDropifyElement.dropify({
        tpl: {
            clearButton: '<button type="button" class="btn btn-square btn-danger btn-delete dropify-clear" id="delete-logo"><i class="fa fa-trash-o"></i></button>',
            message: '<div class="dropify-message"><span class="file-icon" /> <p>' + message + '</p></div>', // style="' + style + '
        }
    });

}

function toggle_checkboxes(checkboxData) {
    let checkboxes = $(".custom-control-input");

    if (checkboxData.is_restaurant) checkboxes.eq(0).prop("checked", true);
    if (checkboxData.is_bar) checkboxes.eq(1).prop("checked", true);
    if (checkboxData.is_wine_shop) checkboxes.eq(2).prop("checked", true)
}

function update_hours_css() {
    let opened;
    let closed;
    if(language === 'FR'){
        opened = 'ouvert';
        closed = 'fermé';
    }else if(language === 'IT'){
        opened = 'aperto';
        closed = 'chiuso';
    }else{
        opened = 'opened';
        closed = 'closed';
    }
    
    let sheet = document.createElement('style');
    sheet.innerHTML = '.opening-hours .switch input:checked ~ .switch-indicator::after {content: "' + opened + '"}' +
        '.opening-hours .switch-indicator::after {content: "' + closed + '"}' +
        '.opening-hours .holidays .switch input:checked ~ .switch-indicator::after {content: "' + closed + '"}' +
        '.opening-hours .holidays .switch-indicator::after {content: "' + opened + '"}';
    document.body.appendChild(sheet);
}

// function description_handler() {
//     let width = $(window).width();
//     let column = $('.col-lg-10');
//     let minWidth = screen.width===1440? 992: 972;
//
//     if (width < minWidth) column.css("padding-left", 'unset');
//     else column.css("padding-left", '25px');
//
//     window.onresize = function () {
//         let width = $(window).width();
//         if (width < minWidth) column.css("padding-left", 'unset');
//         else column.css("padding-left", width / 12);
//     };
// }
