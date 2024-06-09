$(document).ready(function () {
  loadLikes(1);
  $('#clear-search-likes').hide();
});

$('#likes-sorting-dropdown').on('change', function(){
  loadLikes(1);
});

$('#likes-search').on('input', function(){
  if ($(this).val()) {
    $('#clear-search-likes').show();
  } else {
    $('#clear-search-likes').hide();
  }
  loadLikes(1);
});

$('#clear-search-likes').on('click', function() {
  $($(this).siblings('#likes-search')[0]).val('');
  $('#clear-search-likes').hide();
  loadLikes(1);
});

function loadLikes(page, per_page=10) {
  $.ajax({
      url: '/pro/ajax/v2/place-likes/',
      method: 'GET',
      headers: {
          "accept-language": userLang
      },
      data: {
        'place_id': pid,
        'sort_by': $('#likes-sorting-dropdown').val(),
        'search_keyword': $('#likes-search').val(),
        'page': page
      },
      success: function (data) {
          $("#number_of_likes").html(data['count']);
          renderLikes(data['results']);
          renderPagination("#likes-pagination", Math.ceil(data['count'] / per_page), page);
      },
      error: function (req, err) {
          console.log(err)
      }

  });
}

function renderLikes(data) {
  html = ''
  for (var i = 0; i < data.length; i++) {
      var source = $("#like-template").html();
      var template = Handlebars.compile(source);

      var context = data[i]
      html += template(context);
  }

  $("#likes_list").html(html);
}
