var pdg_widget = null;
var all_places_by_ids = {};
var all_subscriptions_by_ids = {};

function select_place_init(){
    $("#id_type").change(function() {
        var user_type = $(this).val();
        if(user_type == 40) {
            $("#place_selector").css('display', 'block');
            $("#customer_id").css('display', 'block');
            $("#subscription_id").css('display', 'block');
        } else {
            $("#place_selector").css('display', 'none');
            $("#customer_id").css('display', 'none');
            $("#subscription_id").css('display', 'none');
        }
    });

    select_place = $('#id_place').select2({
        allowClear: true,
        width: '100%',
        placeholder: 'Select Establishment for Owner...',

        dropdownParent: $('#place_selector'),
        ajax: {
            url: url_ajax_published_places_list,
            dataType: 'json',
            delay: 250,
            data: function (params) {
                return {
                    q: params.term,
                    page: params.page,
                };
            },
          processResults: function (data, params) {
            for (var i in data.items){
                var item0 = data.items[i];
                all_places_by_ids[item0.id] = item0;
              }
              params.page = params.page || 1;
              return {
                results: $.map(data.items, function(item){
                  if (item.name){
                    item.text = $('<span><strong>' + item.name + '</strong>: ' + item.street_address + item.zip_code + item.city + item.country + '</span>');
                    return item;
                  }
                }),
                pagination: {
                    more: (params.page * 30 ) < data.total_count
                  }
                };
              },
            },
            cache: true,
        });
}

function load_subscriptions(customer_id){
  select_subscription = $('#id_subscription').select2({
      allowClear: true,
      width: '100%',
      dropdownParent: $('#subscription_id'),
      placeholder: 'Select Subscription for Place...',
      ajax: {
          url: url_ajax_subscriptions_list,
          dataType: 'json',
          delay: 250,
          data: { 'customer': customer_id },
          processResults: function (data) {
              for (var i in data.items){
                  var item0 = data.items[i];
                  all_subscriptions_by_ids[item0.id] = item0;
              }
              return {
                  results: $.map(data.items, function(item){
                      return {
                          text: item.list_format,
                          id: item.id,
                      };
                  }),
              };
          },
          cache: true,
          error: function(data){
            console.log(data);
          }
      }
  });
}


$(document).ready(function(){
    pdg_widget = new PDG_Widget({});
    pdg_widget.init();

    $('#user-edit-form').change(function() {
      $("#userActions").addClass("disabledDiv");
    });

    $("#btn_renew_password").click(function(){
        var jsonArray = {
            "username": username,
        };

        $.ajax({
                type: "POST",
                dataType: "json",
                url: url_reset_password,
                data: jsonArray,
                success: function(data) {
                    $("#modal_renew_password").modal("toggle");
                },
                error: function(data){
                    console.warn(data);
                }
        });
    });

    $("#btn_resend_activation").click(function(){
        var jsonArray = {
            "username": username,
            "action": "resend_activation"
        };

        $.ajax({
                type: "POST",
                dataType: "json",
                url: url_reset_password,
                data: jsonArray,
                success: function(data) {
                    $("#modal_resend_activation").modal("toggle");
                },
                error: function(data){
                    console.warn(data);
                }
        });
    });

    if(password_changed){
        $("#modal_update_password").modal("toggle");
    }

    select_place_init();
    customer_id = $('#id_customer').attr('value');
    load_subscriptions(customer_id);

    $('#id_customer').change(function(){
      customer_id = $('#id_customer').val();
      load_subscriptions(customer_id);
      if ($('#id_customer').val() == ''){
        $('#id_subscription').val(null).trigger('change');
      }
    });
});
