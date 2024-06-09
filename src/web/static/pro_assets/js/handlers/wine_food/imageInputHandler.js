// When user clicks delete image button, image is replaced by default image
function replace_wine_image(add = false) {
    let default_image = missingWineImage;
    let wineImageId = "#wine-image";

    if (add) {
        wineImageId += "-add"
    }

    $(wineImageId).attr('src', default_image);
}

function replace_food_image(add = false) {
    let default_image = missingFoodImage;
    let foodImageId = "#food-image";

    if (add) {
        foodImageId += "-add"
    }
    $(foodImageId).attr('src', default_image);

}

// Clears image preview to it's previous preview
function clear_image_input(formId, hideErrors = false) {
    let imageInput = "#modify-image-" + formId;
    let error = image_error(formId);

    if (hideErrors) {
        $(error.extensionError).slideUp();
        $(error.sizeError).slideUp();
        $('[id^=missing-image-error]').hide();
    }
    $(imageInput).val('')
}

// Invokes image validation
function upload_image(input, idNaming, formId) {
    let imageId = "#" + idNaming + "-image";

    if (input.files && input.files[0]) {
        $('[id^=missing-image-error]').slideUp();
        validate_image(input, imageId, formId);
    }
}

function validate_image(image, imageId, formId) {
    let _fileExtensions = ["png", "jpg", "gif", "jpeg", "heic"];
    let imageExtension = image.files[0].name.split('.').pop().toLowerCase();
    let error = image_error(formId);

    // Image extension validation
    if (_fileExtensions.includes(imageExtension) === false) {
        $(error.extensionError).slideDown("slow");
        $(error.sizeError).slideUp("slow");
        clear_image_input(formId)
    } else {
        // Image size validation
        let picSize = image.files[0].size;
        if (picSize > 5000000) {
            $(error.sizeError).slideDown("slow");
            $(error.extensionError).slideUp("slow");
            clear_image_input(formId)
        } else {
            $("#picture-removed").val("");
            $("#picture-removed-food").val("");
            let reader = new FileReader();

            $(error.extensionError).slideUp("slow");
            $(error.sizeError).slideUp("slow");

            reader.onload = function (e) {
                if (formId === "add") {
                    imageId += "-add"
                }
                convert_heic(image.files[0], imageId, e.target.result)
            };
            reader.readAsDataURL(image.files[0]);
        }
    }
}

function image_error(idNaming) {
    return {
        "extensionError": "#extension-error-" + idNaming,
        "sizeError": "#size-error-" + idNaming
    }
}
