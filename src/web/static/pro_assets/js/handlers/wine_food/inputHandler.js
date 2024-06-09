function validate_year_input(e, add = false) {
    let yearFormat = "^\\d{4}$";
    let yearInputId = "#wine-year";
    let yearErrorId = "#year-error";
    let prevented = 0;

    if (add) {
        yearInputId += "-add";
        yearErrorId += "-add";
    }

    let yearInput = $(yearInputId).children()[0].value;
    if (!yearInput || yearInput === "0") {
        $(yearInputId).children().eq(0).val(0);
        return prevented;
    }
    if (!yearInput.match(yearFormat)) {
        e.preventDefault();
        prevented++;
        $(yearErrorId).slideDown("slow");
    } else {
        $(yearErrorId).slideUp("slow");
    }
    return prevented;
}

function check_price_element(element_path, element_path_error, e) {
    let prevented = 0;
    let price = $(element_path).val();
    $(element_path_error).slideUp("slow");
    if (price != undefined && price != null && price != '') {
        price = price.replace(",", ".");
        let priceFloat = parseFloat(price);
        if (isNaN(priceFloat) || priceFloat != price) {
            prevented++;
            e.preventDefault();
            $(element_path_error).slideDown("slow");
        }
    }
    return prevented;
}

function validate_price(e) {
    return check_price_element("#wine-price", "#price-error", e);
}

function validate_add_wine_price(e) {
    return check_price_element("#wine-price-add", "#price-add-error", e);
}

function validate_typeahead_inputs(e) {
    let prevented = 0;
    let name = $('#n-ame-typeahead').val();
    let winemakers = $('#winemakers-typeahead').val();
    let domain = $('#domain-typeahead').val();
    let image_is_missing = $('#wine-image').attr('src').includes("/static/pro_assets/img/wines/void.gif");

    prevented += validate_price(e);

    if(image_is_missing) {
        e.preventDefault();
        prevented++;
        $('#missing-image-error').slideDown("slow");
    } else {
        $('#missing-image-error').slideUp("slow");
    }
    if (!name) {
        e.preventDefault();
        prevented++;
        $('#name-error').slideDown("slow");
    } else {
        $('#name-error').slideUp("slow");
    }
    if (!winemakers) {
        e.preventDefault();
        prevented++;
        $('#winemakers-error').slideDown("slow");
    } else {
        $('#winemakers-error').slideUp("slow");
    }
    if (!domain) {
        e.preventDefault();
        prevented++;
        $('#domain-error').slideDown("slow");
    } else {
        $('#domain-error').slideUp("slow");
    }
    return prevented;
}

function validate_add_wine_inputs(e) {
    let prevented = 0;
    let name = $('#n-ame-typeahead-add').val();
    let winemakers = $('#winemakers-typeahead-add').val();
    let domain = $('#domain-typeahead-add').val();
    let image_is_missing = $('#wine-image-add').attr('src').includes("/static/pro_assets/img/wines/void.gif");

    prevented += validate_add_wine_price(e);

    if(image_is_missing) {
        e.preventDefault();
        prevented++;
        $('#missing-image-error-add').slideDown("slow");
    } else {
        $('#missing-image-error-add').slideUp("slow");
    }
    if (!name) {
        e.preventDefault();
        prevented++;
        $('#name-error-add').slideDown("slow");
    } else {
        $('#name-error-add').slideUp("slow");
    }
    if (!winemakers) {
        e.preventDefault();
        prevented++;
        $('#winemakers-error-add').slideDown("slow");
    } else {
        $('#winemakers-error-add').slideUp("slow");
    }
    if (!domain) {
        e.preventDefault();
        prevented++;
        $('#domain-error-add').slideDown("slow");
    } else {
        $('#domain-error-add').slideUp("slow");
    }
    return prevented;

}

function validate_add_food_inputs(e, idNaming) {
    let nameId = "#food-name-" + idNaming;
    let descriptionId = "#food-description-" + idNaming;
    let nameErrorId = "#name-error-" + idNaming;
    let descriptionErrorId = "#description-error-" + idNaming;
    let prevented = 0;
    let image_is_missing = $('#food-image-add').attr('src').includes("/static/pro_assets/img/food/food-void-min.png");


    if(image_is_missing) {
        e.preventDefault();
        prevented++;
        $('#missing-image-error-add').slideDown("slow");
    } else {
        $('#missing-image-error-add').slideUp("slow");
    }

    let name = $(nameId).val();
    let description = $(descriptionId).val();
    if (!name) {
        e.preventDefault();
        prevented++;
        $(nameErrorId).slideDown("slow");

    } else {
        $(nameErrorId).slideUp("slow");
    }

    $(nameId).blur(function()
    {
        if( !$(this).val() ) {
            e.preventDefault();
            prevented++;
            $(nameErrorId).slideDown("slow");
        }else{
            $(nameErrorId).slideUp("slow");
        }
    });

    if (!description) {
        e.preventDefault();
        prevented++;
        $(descriptionErrorId).slideDown("slow");

    } else {
        $(descriptionErrorId).slideUp("slow");
    }


    $(descriptionId).blur(function()
    {
        if( !$(this).val() ) {
            e.preventDefault();
            prevented++;
            $(descriptionErrorId).slideDown("slow");
        }else{
            $(descriptionErrorId).slideUp("slow");
        }
    });

    return prevented;
}

function select_add_wine_color(colorValue, add = true) {
    let colorSelect = add ? "#wineColor-add" : "#wineColor";

    if (colorValue) {
      $(colorSelect).val(colorValue.toString());
      $(colorSelect).selectpicker("refresh");
    }
}


function disable_enter_submission() {
    disable_input_submission(".form-control");
    disable_input_submission(".form-group");
    disable_form_submission("#edit-form");
    disable_form_submission("#food-edit-form");
    disable_form_submission("#add-form");
    disable_form_submission("#food-add-form");

}

function disable_input_submission(element) {
    $(element).keydown(function (event) {
        if (event.keyCode === 13) {
            event.preventDefault();
        }
    })
}

function disable_form_submission(form) {
    $(form).submit(function (e) {
        if (e.isTrigger === 3) e.preventDefault();
    });
}

function clear_edit_comment_input() {
    $("#wine-comment-input").val('');
}

function uncheck_is_sparkling() {
    $('input[type="checkbox"]').prop("checked", false);
}

function clear_add_inputs() {
    $('#select2-n-ame-typeahead-add-container').text("");
    $('#select2-n-ame-typeahead-add-container').trigger("change");
    $("#n-ame-typeahead-add").val('');
    $("#winemakers-typeahead-add").val('');
    $("#domain-typeahead-add").val('');
    $("#wine-year-input-add").val('');
    $("#wine-grape-variety-add").val('');
    $("#wine-comment-input-add").val('');
    $("#wine-price-add").val('');
}

function clear_food_inputs() {
    $("#food-name-add").val('');
    $("#food-description-add").val('');
}

function hide_errors(add = false) {
    let yearErrorId = '#year-error';
    let nameErrorId = '#name-error';
    let winemakersErrorId = '#winemakers-error';
    let domainErrorId = '#domain-error';
    let missingImageErrorId = '#missing-image-error';

    if (add) {
        yearErrorId += '-add';
        nameErrorId += '-add';
        winemakersErrorId += '-add';
        domainErrorId += '-add';
    }

    $(yearErrorId).hide();
    $(nameErrorId).hide();
    $(winemakersErrorId).hide();
    $(domainErrorId).hide();
}

function update_domain_name(data, add) {
    let domain = $("#domain-typeahead" + add);
    domain.val(data['domain']);
    if (data['domain'] !== '') domain.parents().eq(3).addClass("form-group do-float");
}

function update_typeahead_inputs(data, add) {
    let winemaker = $("#winemakers-typeahead" + add);
    let domain = $("#domain-typeahead" + add);
    let year = add ? $("#wine-year-input" + add) : $("#wine-year-id");
    let grapeVariety = $("#wine-grape-variety" + add);

    if(add != undefined && add != null && add != '' && data['wineId'] != undefined && data['wineId'] != null && data['wineId'] != '') {
        $("#wine-id-autocomplete-add").val(data['wineId']);
    }

    if (data['isSparkling'] === true) $('input[type="checkbox"]').prop("checked", true);
    select_add_wine_color(data['wineColor'], add);

    winemaker.val(data['winemakers']);
    domain.val(data['domain']);
    year.val(data['wineYear']);
    grapeVariety.val(data['wineGrapeVariety']);

    if (data['winemakers'] !== '') winemaker.parents().eq(3).addClass("form-group do-float");
    if (data['domain'] !== '') domain.parents().eq(3).addClass("form-group do-float");
    if (data['wineYear'] !== '') year.parents().eq(3).addClass("form-group do-float");
    if (data['wineGrapeVariety'] !== '') grapeVariety.parents().eq(3).addClass("form-group do-float");
}

function get_domain_info(e, url, add) {
    get_domain_info_on_mouse_click(url, add);
    if (event.keyCode === 13) {
        let data = {'winemaker': e.currentTarget.value};
        get_domain_name(url, data, add)
    }
}

// Gets data for selected wine name and then according to id, updates all quickpreview fields
function get_wine_by_name(url, data, add) {
    $.ajax({
        url: url,
        type: 'post',
        async: false,
        dataType: 'json',
        data: data,
        success: function (data) {
            if (Object.keys(data).length !== 0) update_typeahead_inputs(data, add)
        },
        error: function (xhr, status, error) {
            console.log(error);
        }
    });
}

// Calls for selected winemakers domain
function get_domain_name(url, data, add) {
    $.ajax({
        url: url,
        type: 'post',
        async: false,
        dataType: 'json',
        data: data,
        success: function (data) {
            if (Object.keys(data).length !== 0) update_domain_name(data, add)
        },
        error: function (xhr, status, error) {
            console.log(error);
        }
    });
}

function get_domain_info_on_mouse_click(url, add) {
    let container = $("#winemakers-typeahead" + add).parents().eq(2).children();
    if (container.length === 2) {
        let results = container.eq(1);
        results.unbind('click');
        results.on('click', function (e) {
            let data = {'winemaker': e.target.innerText};
            changed += 1;
            get_domain_name(url, data, add)
        })
    }
}


// Gets results for typeahead source
function get_ajax_list_data(url) {
    var result = null;

    $.ajax({
        url: url,
        type: 'get',
        dataType: 'json',
        async: false,
        success: function (data) {
            result = data.result;
        }
    });
    return result;
}

function wine_change_listener(add) {
    add_change_listener("#n-ame-typeahead" + add);
    add_change_listener("#winemakers-typeahead" + add);
    add_change_listener("#domain-typeahead" + add);
    add_change_listener("#wine-grape-variety" + add);
    add_change_listener("#wine-year-id" + add);
    add_change_listener("#modify-image-edit");
    add_change_listener("wine-comment-input" + add);
    add_change_listener("#wine-price" + add);
    $("#wineColor").on('change', function () {
        changed += 1
    });

    if (add) {
        add_change_listener("#modify-image-add");
        $("#n-ame-typeahead-add").bind('keydown', function () {
            changed += 1
        });
        $("#wine-year-input-add").bind('keydown', function () {
            changed += 1
        });
    }

    $('input[type="checkbox"]').on('change', function () {
        changed += 1
    })
}

function food_change_listener(namingId) {
    add_change_listener("#food-name-" + namingId);
    add_change_listener("#food-description-" + namingId);
    add_change_listener("#modify-image-" + namingId + "-food");
}

// If there were any input changes, we want to trace them so we can invoke SAVE BEFORE LEAVE modal
function add_change_listener(element) {
    $(element).on('input', function () {
        changed += 1
    })
}

// Initializes wine alerts
function wine_alerts(dashboard) {
    if (!dashboard) generate_alert("#qv-product-add", true, false);
    generate_alert("#qv-user-details", true, false)
}

// Initializes food alerts
function food_alerts(dashboard) {
    let id = dashboard ? "#food-user" : "#food-user-details";
    if (!dashboard) generate_alert("#qv-product-add", true, true);
    generate_alert(id, true, true)
}

// SAVE BEFORE LEAVING invocation on focus out and redirection to other pages
function generate_alert(elementId, handler, food = false) {
    let product = $(elementId);
    // If quickpreview window class changes it means that it's closing
    // we want to validate previously if there were made changes in preview and possibly show SAVE BEFORE LEAVING modal
    product.on('cssClassChanged', function (e) {
        // Check if e.target or product.attr class if pointing on quickpreview modal
        if (product.attr('class') === "quickview quickview-lg wineslider" &&
            $(e.target).attr('class') === "quickview quickview-lg wineslider" ||
            product.attr('class') === "quickview quickview-lg wineslider form-group do-float" &&
            $(e.target).attr('class') === "quickview quickview-lg wineslider form-group do-float") {
            // If there were any changes we want to invoke the modal
            if (changed > 0) {
                modal_handler(e, product, food);
                if (handler) {
                    $(document).on('click', function (event) {
                        if (!$(event.target).closest("#add-form, #edit-form, #save, #popup-autoshow, #food-add-form, food-edit-form").length) {
                            if (changed > 0) {
                                if ($(event.target).attr("class") === "title") {
                                    event.preventDefault();
                                    // $("#save").modal('toggle');
                                    $("#dismiss").one("click", function () {
                                        $(event.target).offsetParent()[0].click()
                                    })

                                } else {
                                    // $("#save").modal('toggle');
                                }

                            }
                        }
                    });
                }
            }
        }
    });
}

// Handler for SAVE BEFORE LEAVING modal
function modal_handler(e, product, food) {
    // $(e.target).attr('class', "quickview quickview-lg wineslider reveal");
    // $("#save").modal('toggle');

    // Close modal without saving
    $("#dismiss").one("click", function () {
        product.attr('class', "quickview quickview-lg wineslider");
        changed = 0
    });

    // Save changes clicking from modal
    $("#no-dismiss").on("click", function () {
        // Gets button depending on visible button text
        let updateButton = $(product).find("button:contains('UPDATE')").length === 0 ? $(product).find("button:contains('POST')") : $(product).find("button:contains('UPDATE')");
        let prevented = 0;

        // Food operation handler - validates inputs and then saves changes by clicking on button or highlights form errors
        if (food) {
            if (updateButton.attr('id') === 'post-edit' || updateButton.attr('id') === 'post-edit-food') { // updateButton.attr('id') === 'post-edit-food' handles dashboard food update
                prevented += validate_add_food_inputs(e, "edit");
                if (prevented === 0) updateButton.trigger('click')
            } else {
                prevented += validate_add_food_inputs(e, "add");
                if (prevented === 0) updateButton.trigger('click')
            }

            // Wine operation handler - validates inputs and then saves changes by clicking on button or highlights form errors
        } else {
            if (updateButton.attr('id') === 'post-edit') {
                prevented += validate_year_input(e);
                prevented += validate_typeahead_inputs(e);
                if (prevented === 0) {
                    e.preventDefault();
                    updateButton.click()
                }
            } else {
                prevented += validate_year_input(e, true);
                prevented += validate_add_wine_inputs(e);
                if (prevented === 0) {
                    e.preventDefault();
                    updateButton.click()
                }
            }
        }
    });


}

// Handles POST and EDIT actions
function post_data(event, state, formId, postType, food) {
    let modal = $(state);
    let form = $(formId);

    let suffix = food ? postType + '-food' : postType;
    let image = $("#modify-image-" + suffix);
    let entries = get_entries_values();
    let formData = new FormData(form.get(0));
    let sparklingChanged;
    let isSparkling;
    let previousWineColor;
    let currentWineColor;

    if (!food) {
        isSparkling = !!formData.get("isSparkling");
        sparklingChanged = isSparkling !== JSON.parse($("#wine-sparkling-input").val());
        previousWineColor = parseInt($("#wine-color-input").val());
        currentWineColor = parseInt(formData.get("wineColor"));
    }
    changed = 0;

    formData.append('postType', postType);
    formData.append(image.prop("name"), image.prop('files')[0]);
    // modal.parents().eq(1).attr('class', "quickview quickview-lg wineslider");
    food ? show_list_loading_icon("food") : show_wine_loading_icon(entries, previousWineColor, currentWineColor, sparklingChanged, postType, isSparkling);
    
    $("#qv-product-add").removeClass('reveal');
    $('#qv-product-add').attr("class","quickview quickview-lg wineslider");
    $.ajax({
        headers: {
            'X-CSRFToken': formData.get('csrfmiddlewaretoken')
        },
        data: formData,
        type: form.attr('method'),
        url: form.attr('action'),
        processData: false,
        contentType: false,
        success: function (response) { // on success..
            if (food) post_render_food(entries);
            else post_render_single_wine(entries, previousWineColor, currentWineColor, sparklingChanged, postType, isSparkling);
            $(".app-backdrop.backdrop-quickview").remove();
            $(".spinner-dots-list").hide();
        },
        error: function (data) {
            console.warn(data);
        }
    });
}

// Handles post deletion
function delete_data(event, formId, postType, dataModal, food, refresh) {
    let form = $(formId);
    let entries = get_entries_values();
    let formData = new FormData(form.get(0));
    let currentWineColor = parseInt($("#wine-color-input").val());
    let currentSparkling = ($("#wine-sparkling-input").val() == 'true') ? true : false;

    changed = 0;

    formData.append('postType', postType);
    // $('.custom-preloader').show();
    $(dataModal).attr('class', "quickview quickview-lg wineslider");
    food ? show_list_loading_icon("food") : show_wine_loading_icon(entries, currentWineColor, currentWineColor, false, 'delete',
        currentSparkling);

    $.ajax({ // create an AJAX call...
        headers: {
            'X-CSRFToken': formData.get('csrfmiddlewaretoken')
        },
        data: formData, // get the form data
        type: form.attr('method'), // GET or POST
        url: form.attr('action'), // the file to call
        processData: false,
        contentType: false,
        success: function (response) {
            if (refresh) {
                location.reload();
                return 0;
            }
            if (food) post_render_food(entries);
            else post_render_single_wine(entries, currentWineColor, currentWineColor, false, 'delete',
                currentSparkling);
            $(".app-backdrop.backdrop-quickview").remove(); // Hides quickview modal
        },
        error: function (data) {
            console.warn(data);
        }
    });
}

function post_render_wines(entries) {
    if (overscopePage != 'dashboard') {
      render_template('red');
      render_template('white');
      render_template('sparkling');
      render_template('pink');
      render_template('orange');
      wait_until_table_update(5);
    }
}

function post_render_food(entries) {
    show_list_loading_icon("food");
    if (overscopePage != 'dashboard') {
      render_template('food');
    } else {
      render_dashboard_food();
    }
    wait_until_table_update(1);

}

function show_wine_loading_icon(entries, previous_color, color, sparklingChanged, postType, isSparkling) {
    let wineData = get_wine_data(entries, color);
    if (postType === "add") {
        if (isSparkling) wineData = get_wine_data(entries, "sparkling");
        show_list_loading_icon(wineData[2])

        // Changing wine sparkling status handler
    } else if (sparklingChanged && !isSparkling) {
        let sparklingWineData = get_wine_data(entries, "sparkling");
        show_list_loading_icon(wineData[2]);
        show_list_loading_icon(sparklingWineData[2]);

        // Changing wine color handler
    } else if (color !== previous_color) {
        let previousWineData = get_wine_data(entries, previous_color);
        show_list_loading_icon(wineData[2]);
        show_list_loading_icon(previousWineData[2]);
        // Updating wine without color / sparkling change
    } else {
        let sparklingWineData = get_wine_data(entries, "sparkling");
        if (isSparkling) {
            show_list_loading_icon(wineData[2]);
            show_list_loading_icon(sparklingWineData[2]);

        } else {
            show_list_loading_icon(wineData[2]);

        }
    }
}

function post_render_single_wine(entries, previous_color, color, sparklingChanged, postType, isSparkling) {
    let wineData = get_wine_data(entries, color);

    // Adding new wine handler
    if (postType === "add") {
        if (isSparkling) wineData = get_wine_data(entries, "sparkling");
        window.location.hash = wineData[2];
        render_updated_templates([wineData]);

        // Changing wine sparkling status handler
    } else if (sparklingChanged && !isSparkling) {
        let sparklingWineData = get_wine_data(entries, "sparkling");
        window.location.hash = sparklingWineData[2];
        render_updated_templates([wineData, sparklingWineData])

        // Changing wine color handler
    } else if (color !== previous_color) {
        let previousWineData = get_wine_data(entries, previous_color);
        window.location.hash = previousWineData[2];
        render_updated_templates([wineData, previousWineData]);

        // Updating wine without color / sparkling change
    } else {
        let sparklingWineData = get_wine_data(entries, "sparkling");

        window.location.hash = isSparkling ? sparklingWineData[2] : wineData[2];
        if (isSparkling) {
            render_updated_templates([wineData, sparklingWineData]);
        } else {
            render_updated_templates([wineData]);
        }
    }

}

function render_updated_templates(winesData) {
    winesData.forEach(function (wine) {
        show_list_loading_icon(wine[2]);
        if (overscopePage != 'dashboard') {
          render_template('red');
          render_template('white');
          render_template('sparkling');
          render_template('pink');
          render_template('orange');
        } else {
          render_dashboard_wines();
        }
    });
    wait_until_table_update(winesData.length);

}

function get_wine_data(entries, color) {
    let wineColorName = get_wine_color_name(color);
    let wineEntries = get_wine_list_entries(entries, color);
    let wineColorUrl = wineListUrl;

    return [wineEntries, wineColorUrl, wineColorName]
}

function get_wine_list_entries(entries, color) {
    let entriesObject = {10: entries[0], 20: entries[1], "sparkling": entries[2], 30: entries[3], 40: entries[4]};
    return entriesObject[color]
}

function get_wine_color_name(color) {
    let colors = {10: "red", 20: "white", 30: "pink", 40: "orange", "sparkling": "sparkling"};
    return colors[color]
}

function show_list_loading_icon(naming1, naming2) {
    let table = $("#result-" + naming1);
    let columns = table.find('div[class^="col-xl-6"]');
    columns.each(function () {$(this).addClass('opacity-0');});
    table.children().eq(0).show();
    if (naming2) {
        $("#result-" + naming2).children().eq(0).show()
    }
}


// Gets number of visible entries for all lists on page -> [10, 50, 100, All]
function get_entries_values() {
    let entries = [];
    $("[id^='list-select']").each(function (index, element) {
        entries.push(parseInt($(element).val()))
    });
    return entries
}

function handle_sorting_selection() {
    $("[id^='list-select-sorting-']").on('change', function () {
        idNaming = this.id.replace("list-select-sorting-", '')
        show_list_loading_icon(idNaming);
        render_template(idNaming);
        wait_until_table_update(1);
    });
}

// ------------------------------------------------- LOADING PAGE ---------------------------------------------------------
function wait_until_wines_load() {
    let loaded = 0;
    $("div[id^='result-'].row").each(function (index, element) {
        if ($(element).children().children().length === 0) return setTimeout(wait_until_wines_load, 1000);
        loaded += 1;
    });
    if (loaded === 5) $('.custom-preloader').fadeOut("slow");
    if (location.hash) shiftWindow();
}

function wait_until_foods_load() {
    let loaded = 0;
    $("div[id^='result-'].row").each(function (index, element) {
        if ($(element).children().children().length === 0) return setTimeout(wait_until_foods_load, 1000);
        loaded += 1;
    });
    if (loaded === 1) $('.custom-preloader').fadeOut("slow");
}

function wait_until_table_update(tablesNumber) {
    let loaded = 0;
    $("div[id^='result-'].row").each(function (index, element) {
        $(element).one('DOMSubtreeModified', function () {
            loaded += 1;
            if (loaded === tablesNumber) {
                $('.custom-preloader').fadeOut("slow");
                $('.spinner-dots-list').fadeOut("slow");
            }
        })
    });

}

function change_remove_class_function() {
    (function () {
        var originalAddClassMethod = jQuery.fn.removeClass;

        jQuery.fn.removeClass = function () {
            var result = originalAddClassMethod.apply(this, arguments);
            jQuery(this).trigger('cssClassChanged');
            return result;
        }
    })();
}

function removeHash() {
    history.pushState("", document.title, window.location.pathname
        + window.location.search);
}

function shiftWindow() {
    let anchorHash = window.location.href.toString();
    anchorHash = anchorHash.substr(anchorHash.lastIndexOf('#'));
    $('html, body').animate({
        scrollTop: $(anchorHash).offset().top - 70
    }, 500);
}
