change_remove_class_function();

window.addEventListener("hashchange", shiftWindow);


// ACTION: Re-render wine tables on entries amount change, this.value = entries amount
$(document).on('change', '[id^="list-select-per-page"]', function () {
    let idNaming = this.id.replace("list-select-per-page-", "");
    let filterValue = $("#filter-" + idNaming).val();

    if (filterValue) render_template(idNaming, true);
    else render_template(idNaming, true);
});


$('[id^="list-search"]').on('input', function () {
    let idNaming = "allcolors";

    if ($(this).val()) {
        $("#category-title-" + idNaming).html(you_search_text + ': ' + $(this).val());
        $("#allcolors").show();
        $('#clear-search').show();
        $('.media-list:not(#allcolors)').hide();
    } else {
        $("#category-title-" + idNaming).html(section_titles[idNaming]);
        $("#allcolors").hide();
        $('#clear-search').hide();
        $('.media-list:not(#allcolors)').show();
    }

    render_template(idNaming);
});

$('#clear-search').on('click', function() {
  $($(this).siblings('[id^="list-search"]')[0]).val('');
  $("#allcolors").hide();
  $('.media-list:not(#allcolors)').show();
});

$.urlParam = function (name) {
  var urlParamResults = new RegExp('[\?&]' + name + '=([^&#]*)').exec(window.location.search);
  return (urlParamResults !== null) ? urlParamResults[1] || 0 : false;
}

var intervalID = setInterval(function(){
  if (window.loadedElements == 6) {
    if (!window.scrolled && $.urlParam('scrollTo')) {
      $(window).scrollTo("#result-" + $.urlParam('scrollTo'), {
        'offset': {left:0, top:-150}
      });
      window.scrolled = true;
    }
  }
}, 1000);


app.ready(function () {
    window.scrolled = false;
    window.loadedElements = 0;

    // ACTION: At the beginning, render all tables with entries in table set to 10
    if (overscopePage != 'dashboard') {
      render_template("red");
      render_template("white");
      render_template("sparkling");
      render_template("pink");
      render_template("orange");
      render_template("allcolors");
    }

    wait_until_wines_load();
    handle_sorting_selection();
    disable_enter_submission();
    wine_alerts();

    if (overscopePage != 'wines_by_users'){
      handle_wine_edit();
    }
    $('#clear-search').hide();
    $("#allcolors").hide();

    // Remove <strong> and </strong> from image src in typeahead results
    $('#typeahead-name input').on('input', function () {
        let typeahead = $('#typeahead-name').find('.typeahead__result');
        if (typeahead.length !== 0) wait_until_list_is_displayed();
    });
    // remove scroll when mouse on typeahead-name
    $('#typeahead-name').on('mouseover', function (){
        $('div.quickview-block').css('overflow', 'hidden').css('height', '100%');
    }).on('mouseout', function (){
        $('div.quickview-block').css('overflow', 'auto').css('height', 'auto');
    });

    // ACTION: Click on wine from table
    $(document).on('click', '.media.media-single.wineclass', function () {
        changed = 0;
        removeHash();
        wine_change_listener('');
        clear_image_input("edit", true);
        clear_edit_comment_input();
        hide_errors();
        render_edit_wine_view(this, winePostUrl);

    });

    // ACTION: Adding image in add wine modal
    $('input[id="modify-image-add"]').change(function () {
        upload_image(this, "wine", 'add');
    });

    // ACTION: Click on add wine button
    $(document).on('click', '.fab.fab-fixed', function () {
        changed = 0;
        removeHash();
        wine_change_listener('-add');
        clear_image_input("add", true);
        replace_wine_image(true);
        clear_add_inputs();
        uncheck_is_sparkling();
        select_add_wine_color(10);
        hide_errors(true);

    });

    $("#wine-comment-input").on("input", function () {
        changed += 1;
    });

    // ACTION: Searching by wine name
    $('[id^="filter-"]').on('input', function () {
        let idNaming = this.id.replace("filter-", "");
        let entries = $("#list-select-" + idNaming).val();

        render_template(idNaming);
    });

    // if (!window.scrolled) {
    //   $(window).scrollTo("#" + $.urlParam('scrollTo'));
    //   window.scrolled = true;
    // }
});

// ACTION: Click on post button in edit wine modal
$(document).on('click', '#post-edit', function (e) {
    validate_year_input(e);
    validate_typeahead_inputs(e);
    if (!e.isDefaultPrevented()) post_data(event, this, "#edit-form", "edit");

});

var count = 0;
// ACTION: Click on post button in add wine modal
$(document).on('click', '#post-add', function (e) {
  var name = $('#n-ame-typeahead-add').val();
  var winemakers = $('#winemakers-typeahead-add').val();
  winemakers = winemakers.replace("&", "%26");
  console.log(winemakers)
  var year = $('#wine-year-input-add').val();
  if (winemakers.includes('&')){

  }
  // var url =  window.location.pathname;
  // var place_id = url.substring(url.lastIndexOf('/') + 1);
  
  $.ajax({
      type        : "GET",
      url         : "/pro/ajax/v2/is-it-an-already-posted-wine?place_id=" + place_id + "&wine_name=" + name + "&winemaker_name=" + winemakers + "&year=" + year,
      success: function(response) {
          if(response.detail == true){
             $("#wineAlreadyPosted").modal('show');
            $('.btn_add_wine_anyway').off("click").on('click', function (e1) {
                  e1.preventDefault();
                  validate_year_input(e, true);
                  validate_add_wine_inputs(e);
                  if (!e.isDefaultPrevented()) post_data(event, this, "#add-form", "add");
            }); 
          }else{
              validate_year_input(e, true);
              validate_add_wine_inputs(e);
              if (!e.isDefaultPrevented()) post_data(event, this, "#add-form", "add");
          }

      },
      error: function(data){
          console.warn(data);
      }
  });


});

$('.quickview-header .close,#qv-product-add footer .btn-secondary').click(function(){
  $("#qv-product-add").attr('class','quickview quickview-lg wineslider');
  $("#qv-product-add").removeClass('reveal')
})

// ACTION: Click on delete button in wine edit modal
$(document).on('click', '#post-delete', function (e) {
    e.preventDefault();
    $("#modal-default").modal('toggle');
    delete_data(event, "#edit-form2", "delete", "#qv-user-details");
});

// ACTION: Update deletion value containing input
$("#image-delete").click(function () {
    $("#picture-removed").val("1");
});
