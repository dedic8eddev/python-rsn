function validate_logo(obj, element) {
    let _fileExtensions = ["png", "jpg", "gif", 'jpeg', 'heic', 'bmp', 'pcx', 'tga', 'tif', 'tiff', 'raw', 'ico', 'webp', 'pic'];
    let imageElement = $("#" + obj + "-image");
    let image = $(element)[0].files[0];
    let imageExtension = image.name.split('.').pop().toLowerCase();
    let error = owner_logo_errors();

    // Image extension validation
    if (_fileExtensions.includes(imageExtension) === false) {
        $(error.extensionError).slideDown("slow");
        $(error.sizeError).slideUp("slow");
        $(element).val("")
    } else {
        // Image size validation
        let picSize = image.size;
        if (picSize > 5000000) {
            $(error.sizeError).slideDown("slow");
            $(error.extensionError).slideUp("slow");
            $(element).val("")
        } else {  // image is OK
            $(error.sizeError).slideUp("slow");
            $(error.extensionError).slideUp("slow");

            let reader = new FileReader();

            reader.onload = function (e) {
                convert_heic($(element)[0].files[0], "#" + obj + "-image", e.target.result)
                imageElement.attr('src', e.target.result)
            };
            reader.readAsDataURL(image);
            if (obj == 'owner'){
              $("#picture-removed").val("");
            } else {
              $("#company-picture-removed").val("");
            }
        }
    }
}

function upload_image(input) {
    if (input.files && input.files[0]) {
        validate_logo('owner', input);
    }
}

function upload_company_image(input) {
    if (input.files && input.files[0]) {
        validate_logo('company', input);
    }
}

function owner_logo_errors() {
    return {
        "extensionError": "#extension-error-owner-logo",
        "sizeError": "#size-error-owner-logo"
    }
}

function hide_errors() {
    let errors = owner_logo_errors();

    $(errors.sizeError).slideUp("slow");
    $(errors.extensionError).slideUp("slow");
}

function delete_picture() {
    let inputFile = $("#owner-image-input");
    let imageElement = $("#owner-image");

    hide_errors();

    inputFile.val("");
    imageElement.attr("src", missingImage)
}

function delete_company_picture() {
    let inputFile = $("#company-image-input");
    let imageElement = $("#company-image");

    hide_errors();

    inputFile.val("");
    imageElement.attr("src", missingImage)
}

function anchor_handler() {
    let anchorHash = window.location.href.toString();
    if (anchorHash.lastIndexOf('#') !== -1) {
        anchorHash = anchorHash.substr(anchorHash.lastIndexOf('#'));
        let anchorElement = $('a[href="' + anchorHash + '"]');
        if (anchorElement.length > 0) {
            anchorElement.trigger('click');
        }
    }
    $(".nav-link").on('click', function () {
        window.location.hash = this.name
    })
}
