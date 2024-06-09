// Scroll on anchor
var shiftWindow = function () {
    scrollBy(0, -70)
};
if (location.hash) shiftWindow();
window.addEventListener("hashchange", shiftWindow);

change_remove_class_function();

// ACTION: Re-render wine tables on entries amount change, this.value = entries amount
$(document).on('change', '[id^="list-select-per-page"]', function () {
    let idNaming = this.id.replace("list-select-per-page-", "");
    let filterValue = $("#filter-" + idNaming).val();

    render_template(idNaming, true);
});


$('[id^="list-search"]').on('input', function () {
    let idNaming = this.id.replace("list-search-", "");
    if ($(this).val()) {
        $('#clear-search').show();
        $("#category-title-" + idNaming).html(you_search_text + ': ' + $(this).val());
    } else {
        $('#clear-search').hide();
        $("#category-title-" + idNaming).html(section_titles[idNaming]);
    }

    render_template(idNaming);
});

$('#clear-search').on('click', function() {
  $('#clear-search').hide();
  $($(this).siblings('[id^="list-search"]')[0]).val('');
  let idNaming = $(this).siblings('[id^="list-search"]')[0].id.replace("list-search-", "");
  $("#category-title-" + idNaming).html(section_titles[idNaming]);
  render_template(idNaming);
});

change_remove_class_function();

app.ready(function () {
    // ACTION: At the beginning, render food table with entries in table set to 10
    if (overscopePage != 'dashboard') {
      render_template("food");
    }
    disable_enter_submission();
    food_alerts();
    wait_until_foods_load();
    handle_sorting_selection();

    handle_food_edit();
    $('#clear-search').hide();

    // ACTION: Click on food from table
    $(document).on('click', '.media.media-single.foodclass', function () {
        changed = 0;
        removeHash();
        food_change_listener('');
        clear_image_input("edit", true);
        hide_errors();

    });

    // ACTION: Click on add food button
    $(document).on('click', '.fab.fab-fixed', function () {
        changed = 0;
        food_change_listener('add');
        clear_image_input("add", true);
        replace_food_image(true);
        clear_food_inputs();
        hide_errors(true);

    });

    // ACTION: Click on delete image button
    $(document).on('click', '#image-delete-food', function () {
        replace_food_image();
    });

    // ACTION: Adding image in edit food modal
    $('input[id="modify-image-edit-food"]').change(function () {
        upload_image(this, "food", "edit");
    });

    // ACTION: Adding image in add food modal
    $('input[id="modify-image-add-food"]').change(function () {
        upload_image(this, "food", "add");
    });

    $('[id^="filter-"]').on('input', function () {
                let type = this.id.replace("filter-", "");
                let entries = $("#list-select-food").val();
                if (this.value.length > 0) render_template(type);
                else render_template(type);
            });
});

// ACTION: Click on post button in edit food modal
$(document).on('click', '#post-add', function (e) {
    validate_add_food_inputs(e, "add");
    if (!e.isDefaultPrevented()) post_data(event, this, "#food-add-form", "add", true);
});

// ACTION: Click on post button in add food modal
$(document).on('click', '#post-edit-food', function (e) {
    validate_add_food_inputs(e, "edit");
    if (!e.isDefaultPrevented()) post_data(event, this, "#food-edit-form", "edit", true);
});

$(document).on('click', '#post-delete', function (e) {
    e.preventDefault();
    $("#modal-default").modal('toggle');
    delete_data(event, "#edit-form2", "delete", "#food-user-details", true);
});

// ACTION: Update deletion value containing input
$("#image-delete-food").click(function () {
    $("#picture-removed-food").val("1");
});
