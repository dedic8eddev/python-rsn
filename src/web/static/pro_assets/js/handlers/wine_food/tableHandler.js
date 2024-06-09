function generate_food_table(data) {
    var html = "<div class=\"card-body\"><div class=\"media-list media-list-hover media-list-divided\">";
    for (var i = 0; i < data.length; i++) {
      var source = $("#food-template").html();
      var template = Handlebars.compile(source);

      var context = data[i]

      html += template(context);
    }

    html += "</div></div>";
    return html;
}

function generate_wine_table(data) {
    var html = "<div class=\"card-body\"><div class=\"media-list media-list-hover media-list-divided\">";
    for (var i = 0; i < data.length; i++) {

        var source = $("#wine-template").html();
        var template = Handlebars.compile(source);

        var context = data[i]

        html += template(context);
    }
    html += "</div></div>";
    return html;
}

function generate_loading_icon_div() {
    return "<div class=\"spinner-dots-list\" style=\"display: none\">" +
        "<img src=\"/static/pro_assets/img/preloading.gif\" alt=\"preloading Raisin Pro website\" width=\"60\" height=\"100\">" +
        "</div>"
}

function prepare_columns_html(idNaming) {
    let html = "";
    let baseId = "result-" + idNaming;
    let loadingIcon = generate_loading_icon_div();

    html += loadingIcon;
    html += "<div class=\"col-xl-6\" id=\"" + baseId + "1" + "\"></div>";
    html += "<div class=\"col-xl-6\" id=\"" + baseId + "2" + "\"></div>";
    return html
}


function render_table(data, page, idNaming, empty) {
    if (empty) {
        let rowId = "#result-" + idNaming;
        let result = "No appropriate translation here."
        if (language === 'FR') {
            result = 'Aucun enregistrement à afficher.';
        } else if (language === 'IT') {
            result = 'Nessun dato da mostrare.';
        } else {
            result = 'No records to display.';
        }
        html = "<div class=\"spinner-dots-list\" style=\"display: none\"><img src=\"/static/pro_assets/img/preloading.gif\" alt=\"preloading Raisin Pro website\" width=\"60\" height=\"100\"></div><div class=\"list-footer flexbox align-items-center py-20 px-20\" style=\"margin: 0 auto;\">" +
            "<p style=\"display:inline-block;\">" + result + "</p></div>";
        $(rowId).html(html)
    } else {
        // Indexing of list starts from 0 so page nr.1 is on index nr 0
        page -= 1;
        var tableGenerator = idNaming === 'food' ? generate_food_table : generate_wine_table;
        var row = '#result-' + idNaming;
        var columnId1 = row + "1";
        var columnId2 = row + "2";

        const half = Math.ceil(data.results.length / 2);
        const firstHalf = data.results.splice(0, half)
        const secondHalf = data.results.splice(-half)

        var columns = prepare_columns_html(idNaming);
        var columnData1 = firstHalf;
        var html = tableGenerator(columnData1);
        var columnData2 = secondHalf;
        var html2 = tableGenerator(columnData2);

        $(row).html(columns);

        $(columnId1).html(html);
        $(columnId2).html(html2);

    }

    window.loadedElements += 1;
}

function add_tooltip_handler() {
    let elements = $(".top-right-icon");
    elements.each(function () {
        let tooltipElement = $(this).find('img');
        let tooltipType = tooltipElement.attr('data-tooltip-type');
        let template = '<div class="tooltip tooltip-TYPE fade bs-tooltip-left show" role="tooltip"><div class="arrow"></div><div class="tooltip-inner"></div></div>';

        if (tooltipType === 'natural') template = template.replace('TYPE', 'primary');
        else if (tooltipType === 'organic') template = template.replace('TYPE', 'warning');
        else if (tooltipType === 'doubt') template = template.replace('TYPE', 'secondary');
        else template = template.replace('TYPE', 'danger');

        $(this).find('img').tooltip({
                template: template,
            }
        );
        $(this).find('img').tooltip('hide');

    })
}

function render_template(idNaming, forceFirstPage=false) {
    idNamingToColor = {
      'red': 10,
      'white': 20,
      'pink': 30,
      'orange': 40,
      'sparkling': 'sparkling'
    }

    sortingOption = $('#list-select-sorting-' + idNaming).val();
    perPageOption = $('#list-select-per-page-' + idNaming).val();
    search_keyword = $('#list-search-' + idNaming).val();

    let currentPage = $('#pagination-' + idNaming + " .active");
    let page = currentPage.length !== 0 ? parseInt(currentPage.text()) : 1;

    $.ajax({
        url: overscopePage.includes('wines') ? wineListUrl : foodListUrl,
        method: 'GET',
        headers: {
            "accept-language": userLang
       },
        data: {
            "sort_by": sortingOption,
            "color": idNamingToColor[idNaming],
            'page_size': perPageOption,
            'page': forceFirstPage ? 1 : page,
            'search_keyword': search_keyword,
            'wines_page': overscopePage,
        },
        success: function (data) {
            if (data.count === 0) {
              render_table(data, page, idNaming, true);
              hide_entries(idNaming)
            } else {
                window[idNaming + "Pages"] = Math.ceil(data.count / perPageOption);
                render_table(data, page, idNaming, false);
                render_pagination(idNaming, page);
                handle_pagination(data, idNaming, data.count); // TODO
                add_tooltip_handler();
                $("#footer-" + idNaming).show();

            }
        },
        error: function (req, err) {
            console.log(err)
        }

    });
}

function generate_pagination_html(startingPage, lastPage, activeElementNumber) {
    var html = "";
    var active = "";
    for (var i = startingPage; i <= lastPage; i++) {
        active = activeElementNumber === i ? "active" : "";
        html += generate_pagination_page(i, active);
    }
    return html;
}

function generate_pagination_page(page, active) {
    return "<li class=\"page-item " + active + "\"><a class=\"page-link\" href='#'>" + page + "</a></li>";
}

function render_pagination(idNaming, current) {
    var paginationId = '#pagination-' + idNaming;
    var html = "<li class=\"page-item\"><a class=\"page-link\" href=\"#\" name=\"previous\"><span class=\"ti-arrow-left\" name=\"previous\"></span></li>";
    var allPages = window[idNaming + "Pages"];

    if (allPages <= 5) html += generate_pagination_html(1, allPages, current); // pagination for 5 visible pages
    else if (current + 4 < allPages) html += generate_pagination_html(current, current + 4, current); // pagination for 5 next pages
    else html += generate_pagination_html(allPages - 4, allPages, current); // pagination for 5 last pages

    html += "<li class=\"page-item\"><a class=\"page-link\" href=\"#\" name=\"next\"><span class=\"ti-arrow-right\" name=\"next\"></span></li>";

    $(paginationId).html(html).show();
}

function handle_pagination(data, idNaming, totalPages) {
    var paginationId = '#pagination-' + idNaming;

    $(paginationId + ".pagination").unbind().on('click', function (e) {
        var previousElementValue = parseInt(document.querySelector(paginationId + ' li.active').textContent);
        var pageNumber;
        var render = true;
        var clickTarget = $(e.target).text();
        var clickTargetArrow = $(e.target).attr('name');

        // Checks if target is A or SPAN since we store there pagination value
        if (e.target.tagName === "A" || e.target.tagName === "SPAN") {
            // Go to previous page if previous page exists
            if (typeof clickTargetArrow !== "undefined" && clickTargetArrow.localeCompare("previous") === 0) {
                if (previousElementValue === 1) {
                    render = false;
                    pageNumber = 1;

                } else {
                    $(paginationId + ' li.active').removeClass('active');
                    pageNumber = previousElementValue - 1;
                    // previousElement.previousSibling.classList.add('active');
                    render_pagination(idNaming, pageNumber, true)

                }
                // Go to next page if next page exists
            } else if (typeof clickTargetArrow !== "undefined" && clickTargetArrow.localeCompare("next") === 0) {
                if (previousElementValue === totalPages) {
                    render = false;
                    pageNumber = totalPages;
                } else {
                    // $(paginationId + ' li.active').removeClass('active');
                    pageNumber = previousElementValue + 1;
                    // previousElement.nextSibling.classList.add('active')
                    render_pagination(idNaming, pageNumber, true);
                }
                // Go to clicked page
            } else if (clickTarget === "...") {
                render = false;
                pageNumber = previousElementValue;
            } else {
                // $(paginationId + ' li.active').removeClass('active');
                pageNumber = parseInt(clickTarget);

                // $(e.target).parent().addClass("active");
                render_pagination(idNaming, pageNumber, true)


                // If clicked page is current page, don't render view
                if (pageNumber === previousElementValue) render = false;

            }

            if (render) render_template(idNaming);
        }
    })
}

function hide_entries(idNaming) {
    let listSelectId = "#footer-" + idNaming;
    $(listSelectId).hide()
}
