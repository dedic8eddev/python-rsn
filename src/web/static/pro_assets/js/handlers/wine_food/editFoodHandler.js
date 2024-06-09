function food_data(clickedFood) {
    let id = clickedFood.id;
    let image_src = clickedFood.getElementsByTagName('img').item(0).src;
    let name = clickedFood.getElementsByClassName('fs-16').item(0).innerText;
    let description = clickedFood.getElementsByClassName('name fs-14').item(0).innerText;

    return {
        "id": id,
        "image": "<img class=\"w-130px h-130px rounded\" id=\"food-image\" src=\"" + image_src + "\" alt=\"food\">",
        "name": name,
        "description": description
    }
}

function render_edit_food_view(clickedFood) {
    let food = food_data(clickedFood);
    set_do_float_food();

    $("#food-id").attr('value', food.id).attr('readonly', true);
    $("#food-id-delete").attr('value', food.id).attr('readonly', true);
    $("#food-img-container").html(food.image);
    $("#food-name-edit").val(food.name);
    $("#food-description-edit").val(food.description);

}

// Prevents edit input fields to be obscured by its parent
function set_do_float_food() {
    $("#food-name-edit").parents().eq(3).addClass("form-group do-float");
    $("#food-ingredients-edit").parents().eq(3).addClass("form-group do-float");
}

function handle_food_edit() {
    // ACTION: Click on food from table
    $(document).on('click', '.media.media-single.foodclass', function () {
        changed = 0;
        food_change_listener('edit');
        clear_image_input('edit', true);
        render_edit_food_view(this);
    });
    $(document).on('click', '#image-delete-food', function () {
        clear_image_input("edit", true);
        replace_wine_image();
    });

    // ACTION: Adding image in edit food modal
    $('input[id="modify-image-edit-food"]').change(function () {
        upload_image(this, "food", "edit");
    });
}
