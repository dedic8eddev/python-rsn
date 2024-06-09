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
    console.log(html)
    return html
}


function render_table(data, idNaming, empty) {
    if (empty) {
        let rowId = "#result-" + idNaming;
        let result;
        
        if(language === 'FR'){
            result = 'Aucun enregistrement à afficher.';
        }else if(language === 'IT'){
            result = 'Nessun dato da visualizzare.';
        }else{
            result = 'No records to display.';
        }        

        
        // let result = language === 'FR' ? 'Aucun enregistrement à afficher.' : 'No records to display.';
        // let result = "No records to display.";
        html = "<div class=\"spinner-dots-list\" style=\"display: none\"><img src=\"/static/pro_assets/img/preloading.gif\" alt=\"preloading Raisin Pro website\" width=\"60\" height=\"100\"></div><div class=\"list-footer flexbox align-items-center py-20 px-20\" style=\"margin: 0 auto;\">" +
            "<p style=\"display:inline-block;\">" + result + "</p></div>";
        $(rowId).html(html)
    } else {
        // Indexing of list starts from 0 so page nr.1 is on index nr 0
        var tableGenerator = idNaming === 'dashboardFoodList' ? generate_food_table : generate_wine_table;
        var row = '#result-' + idNaming;
        var columnId1 = row + "1";
        var columnId2 = row + "2";

        if (idNaming === 'dashboardFoodList') {
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
        } else {
          var columns = prepare_columns_html(idNaming);
          $(row).html(columns);
          html1 = tableGenerator(data.results);
          $(columnId1).html(html1);
        }
    }
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

function render_dashboard_wines() {
    $.ajax({
        url: wineListUrl,
        method: 'GET',
        headers: {
            "accept-language": userLang
        },
        data: {
            'place_id': pid,
            'page_size': 3,
            'page': 1,
        },
        success: function (data) {
            render_table(data, 'dashboardWineList', false);
            add_tooltip_handler();
        },
        error: function (req, err) {
            console.log(err)
        }

    });
}

function render_dashboard_food() {
    $.ajax({
        url: foodListUrl,
        method: 'GET',
        headers: {
            "accept-language": userLang
        },
        data: {
            'place_id': pid,
            'page_size': 6,
            'page': 1,
        },
        success: function (data) {
            render_table(data, 'dashboardFoodList', false);
            add_tooltip_handler();
        },
        error: function (req, err) {
            console.log(err)
        }

    });
}
