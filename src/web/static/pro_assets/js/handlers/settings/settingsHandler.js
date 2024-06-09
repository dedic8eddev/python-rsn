function getCookie(name) {
  var cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    var cookies = document.cookie.split(';');
    for (var i = 0; i < cookies.length; i++) {
      var cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
    }
  }
  return cookieValue;
}

var csrftoken = getCookie('csrftoken');

function select_lang(lang) {
    let langSelect = "#lang";
    $(langSelect).val(lang);
    $(langSelect).selectpicker("refresh");
}

function select_currency(cur) {
    let curSelect = "#currency";
    $(curSelect).val(cur);
    $(curSelect).selectpicker("refresh");
}

app.ready(function () {
    $(".custom-preloader").fadeOut('slow');

    $(function () {
      $('[data-toggle="tooltip"]').tooltip();
    });

    $('.sticky-save').mouseenter(function(e){
      e.stopPropagation();
      $(this).stop().animate();
    });

    $('.sticky-save').mouseleave(function(e){
      $(this).fadeOut();
    });

    function handle_sticky_save(status){
      var $sticky = $('.sticky-save.' + status);
      $sticky.show();
      var timeout = setTimeout(function() {
        if (!$sticky.is(":hover")){
          $sticky.fadeOut();
        }
      }, 5000);
    }

    $('#owner_details_form').find(':input').each(function(){
      add_change_listener($(this));
    });

    $('#company_details_form').find(':input').each(function(){
      add_change_listener($(this));
    });

    function add_change_listener(element) {
        $(element).on('change', function () {
          if (window.location.href.includes('company')){
            post_company_details_data();
          } else {
            post_owner_details_data();
          }
          });
    }

    select_lang(lang);
    select_currency(currency);
    $("#delete-picture").click(function () {
        $("#picture-removed").val("1");
        post_owner_details_data();
    });

    $("#delete-company-picture").click(function () {
        $("#company-picture-removed").val("1");
        post_company_details_data();
    });

    $('input[id="owner-image-input"]').change(function () {
        upload_image(this);
    });

    $('input[id="company-image-input"]').change(function () {
        upload_company_image(this);
    });

    $(document).on('click', '#delete-picture', function () {
        delete_picture();
    });

    $(document).on('click', '#delete-company-picture', function () {
        delete_company_picture();
    });



    function post_owner_details_data(){
      form = $('#owner_details_form');
      var formData = new FormData(form[0]);
      formData.append('ownerImage', $('#owner-image-input').val());

      $.ajax({
          url: postOwnerDetailsFormUrl,
          headers: {
              'X-CSRFToken': csrftoken
          },
          type: 'post',
          processData: false,
          contentType: false,
          data: formData,
          success: function(){
            new_lang = $('select[id="lang"]').children('option:selected').val();
            if (new_lang != lang){
              location.reload();
            }
          },
          error: function (xhr, status, error) {
            handle_sticky_save('error');
            console.log(error);
          },
      });
    }

    function post_company_details_data(){
      form = $('#company_details_form');
      var formData = new FormData(form[0]);
      formData.append('companyImage', $('#company-image-input').val());

      $.ajax({
          url: postCompanyDetailsFormUrl,
          headers: {
              'X-CSRFToken': csrftoken
          },
          type: 'post',
          processData: false,
          contentType: false,
          data: formData,
          error: function (xhr, status, error) {
            handle_sticky_save('error');
            console.log(error);
          },
      });
    }


// -------------------- INVOICES TABLE -------------------------
    status_dict = {
      'not_paid': {
        'en': 'not paid',
        'fr': 'non payé',
        'color': 'red',
        'transform': 'uppercase',
      },
      'paid': {
        'en': 'paid',
        'fr': 'payé',
        'color': 'green',
        'transform': 'capitalize',
      },
      'posted': {
        'en': 'pending',
        'fr': 'expédié',
        'color': 'orange',
        'transform': 'capitalize',
      },
      'payment_due': {
        'en': 'payment due',
        'fr': 'paiement dû',
        'color': 'red',
        'transform': 'capitalize',
      },
      'voided': {
        'en': 'voided',
        'fr': 'annulé',
        'color': 'black',
        'transform': 'capitalize',
      },
      'pending': {
        'en': 'pending',
        'fr': 'en attente',
        'color': 'grey',
        'transform': 'capitalize',
      },
    };


    var ITOptions = {"sLengthMenu": "Mostra Display _MENU_ elementi",
        "sZeroRecords": "Niente trovato - mi dispiace",
        "sInfo": "Mostrando _START_ to _END_ of _TOTAL_ elementi",
        "sInfoEmpty": "Mostrando 0 to 0 of 0 elementi",
        "sInfoFiltered": "(filtrato da _MAX_ total elementi)"
    };

    $('#invoices-table').DataTable({
      responsive:true, 
      ajax: {
          "url": pro_invoices,
          "data": {
            'subscription_id': subscription_id
          },
          "type" : "GET",
          "autoWidth": true
      },
      columns: [
          { "data" : "id" },
          { "data" : "establishment" },
          { "data" : "company" },
          { "data" : "status" },
          { "data" : "date" },
          { "data" : "amount", orderable: false },
      ],
      rowCallback: function(row, data, index) {
        status = data.status;
        $("td:eq(3)", row).css('color', status_dict[status]['color']).css('text-transform', status_dict[status]['transform']).text(status_dict[status][lang_code]);
        row.classList.add('clickable-row');
        row.style.cursor = "pointer";
        row.setAttribute('id', data.id);
      },
      language: {
        url: lang_url
      },
      fnInitComplete: function(oSettings, json) {
        if (is_in_trial){
          $('.dataTables_empty').text(trial_text);
        }
    }
    });

    $('#invoices-table').on('click', 'tr.clickable-row', function (){
      pdf_url = $.ajax({
          url: pro_invoice_pdf_url,
          type: 'get',
          async: false,
          dataType: 'json',
          data: {'id': $(this).attr('id') },
          success: function(data) {
            window.open(data.url, "_self");
          },
          error: function (xhr, status, error) {
              console.log(error);
              return [];
          },
      });

    });

    anchor_handler();
});
