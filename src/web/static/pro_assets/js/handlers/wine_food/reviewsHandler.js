$(document).ready(function () {
  loadReviews(1);
  getTotalUnread();
  $('#clear-search').hide();
  $('.preloader').show();
});

$(document).on('click', '.reviews [data-toggle="quickview"]', function() {
  var uid = $(this).attr('data-uid')
  $(this).find('.avatar').removeClass('status-success');
  $("#qv-messages").attr('data-uid', uid)
  loadComments(uid);
  markAllRead(uid);
});

$(document).on('click', '.delete-comment', function() {
  var uid = $("#qv-messages").attr('data-uid')
  var cid = $(this).attr('data-comment-id')
  $.ajax({
    url: '/pro/ajax/v2/owner-comments/' + cid + '/',
    method: 'DELETE',
    beforeSend: function(xhr) {
      xhr.setRequestHeader('X-CSRFToken', csrftoken);
    },
    success: function (data) {
        loadComments(uid);
    },
    error: function (req, err) {
        console.log(err)
    }
  });
});

$(document).on('click', '.edit-comment', function() {
  var cid = $(this).attr('data-comment-id');
  var initialText = $(this).attr('data-initial-text');
  $('#comment-form-for-' + cid).find('textarea').val(initialText);
  $('#comment-form-for-' + cid).show();
  $('#description-hideable-for-' + cid).hide();
});

$(document).on('click', '.cancel-edit', function() {
  $('[id^="comment-form-for-"]').hide();
  var cid = $(this).attr('data-edit-for');
  $('#description-hideable-for-' + cid).show();
});

$(document).on('click', '.save-edit', function() {
  var uid = $("#qv-messages").attr('data-uid')
  var cid = $(this).attr('data-edit-for');
  var edit_description = $(this).parent().find('textarea').first().val();

  if (edit_description) {
    $.ajax({
      url: '/pro/ajax/v2/owner-comments/' + cid + '/',
      method: 'PATCH',
      data: {
        'description': edit_description
      },
      beforeSend: function(xhr) {
        xhr.setRequestHeader('X-CSRFToken', csrftoken);
      },
      success: function (data) {
          loadComments(uid);
      },
      error: function (req, err) {
          console.log(err)
      }
    });
  }
});

$('#reviews-sorting-dropdown').on('change', function(){
  loadReviews(1);
});

var keyPressTimeout;

$('#reviews-search').on('input', function(){
  if ($(this).val()) {
    $('#clear-search').show();
  } else {
    $('#clear-search').hide();
  }

  clearTimeout(keyPressTimeout);
  keyPressTimeout = setTimeout(function() {
      loadReviews(1);
    },
    500
  );
});

$('#clear-search').on('click', function() {
  $($(this).siblings('#reviews-search')[0]).val('');
  $('#clear-search').hide();
  loadReviews(1);
});

$('.publisher-btn').on('click', function(){
  text = $('.publisher-input').val();

  if (text) {
    uid = $("#qv-messages").attr('data-uid');

    $.ajax({
      url: '/pro/ajax/v2/owner-comments/',
      method: 'POST',
      data: {
        'place_id': pid,
        'description': text,
        'in_reply_to_id': uid
      },
      beforeSend: function(xhr) {
        xhr.setRequestHeader('X-CSRFToken', csrftoken);
      },
      success: function (data) {
          $('.publisher-input').val('');
          loadComments(uid);
      },
      error: function (req, err) {
          console.log(err)
      }
    });
  }
});


function loadReviews(page, per_page=10) {
  $.ajax({
      url: '/pro/ajax/v2/place-reviews/',
      method: 'GET',
      headers: {
          "accept-language": userLang
      },
      data: {
        'place_id': pid,
        'sort_by': $('#reviews-sorting-dropdown').val(),
        'search_keyword': $('#reviews-search').val(),
        'page': page
      },
      success: function (data) {
          $("#number_of_reviews").html(data['count']);
          renderReviews(data['results']);
          renderPagination("#reviews-pagination", Math.ceil(data['count'] / per_page), page);
          $('.preloader').fadeOut(600);
      },
      error: function (req, err) {
          console.log(err)
      }

  });
}

function loadComments(uid) {
  $.ajax({
      url: '/pro/ajax/v2/place-comments/',
      method: 'GET',
      data: {
        'place_id': pid,
        'user_id': uid
      },
      success: function (data) {
        html = '';
        for (var i = 0; i < data.results.length; i++) {
            var source = $("#comment-template").html();
            var template = Handlebars.compile(source);

            var context = data.results[i];
            context['owner_text'] = establishmentOwnerText;
            context['owner_image'] = establishmentOwnerImage;
            html += template(context);
        };

        $("#comments-list").html(html);
      },
      error: function (req, err) {
          console.log(err)
      }
  });
}

function renderReviews(data) {
  html = ''
  for (var i = 0; i < data.length; i++) {
      var source = $("#review-template").html();
      var template = Handlebars.compile(source);

      var context = data[i]
      html += template(context);
  }

  $("#reviews_list").html(html);
}


function getTotalUnread() {
  $.ajax({
      url: '/pro/reviews/' + pid + '/get-total-unread/',
      method: 'GET',
      success: function (data) {
        if (data['total']) {
          ajusted_number = data['total'] > 99 ? '99+' : data['total'];
          $("#total-number-unread").text(ajusted_number);
          $("#total-number-unread").show();
        } else {
          $("#total-number-unread").hide();
        }
      },
      error: function (req, err) {
          console.log(err)
      }
  });
}

function markAllRead(uid) {
  $.ajax({
      url: '/pro/reviews/' + pid + '/read-all-for-user/' + uid + '/',
      method: 'GET',
      success: function (data) {
        getTotalUnread();
      },
      error: function (req, err) {
          console.log(err)
      }
  });
}
