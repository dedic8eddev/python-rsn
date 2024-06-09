function renderPagination(paginationId, total, current) {
  html = ''
  if (total <= 5) html += generatePaginationHtml(1, total, current); // pagination for 5 visible pages
  else if (current + 4 < total) html += generatePaginationHtml(current, current + 4, current); // pagination for 5 next pages
  else html += generate_pagination_html(total - 4, total, current); // pagination for 5 last pages

  var source = $("#pagination-template").html();
  var template = Handlebars.compile(source);
  var context = {
    'inner': html
  }

  $(paginationId).attr('data-total', total);
  $(paginationId).html(template(context)).show();
}

function generatePaginationHtml(startingPage, lastPage, activeElementNumber) {
    var html = "";
    var active = "";
    for (var i = startingPage; i <= lastPage; i++) {
        var activeText = activeElementNumber == i ? "active" : "";

        var source = $("#pagination-page-template").html();
        var template = Handlebars.compile(source);
        var context = {'active': activeText, 'page': i}

        html += template(context);
    }

    return html;
}

$(document).on("click", '.page-link', function(event) {
    if ($(this).parent().parent().attr('id') in paginationConfig) {
      pgId = $(this).parent().parent().attr('id');
      name = $(this).attr('name');
      activePage = parseInt($("#" + pgId).children('.active').children('a').attr('name'));
      numberOfPages = parseInt($("#" + pgId).attr('data-total')); // subtract previous and next pages

      switch (name) {
        case 'previous':
          destination_page = activePage - 1
          break;
        case 'next':
          destination_page = activePage + 1
          break;
        default:
          destination_page = parseInt(name);
      }

      if (destination_page != 0 && destination_page != activePage && destination_page <= numberOfPages) {
        window[paginationConfig[pgId]](destination_page);
      }
    }
});
