var pdg_widget = null;
var pdg_widget_language = null;
var TransEngine = {
  dd_tr_modified: {
  },

  json_decode_translations: function() {
      var dd_tr_source = $("#id_current_translations").val();
      console.log(dd_tr_source)
      if(dd_tr_source == undefined || dd_tr_source == null || dd_tr_source == '') {
          return null;
      }
      var dd_tr_json = JSON.parse(dd_tr_source);
      return dd_tr_json;
  },

  get_selected_language: function() {
      var sel_lang = $("#id_selected_language").val();
      return sel_lang;
  },

  get_current_contents: function() {
      var contents = $("#id_quote_textarea").val();
      return contents;
  },

  show_lang_version: function() {
        console.log("barev")
      var lang_ver = TransEngine.get_selected_language();
        console.log(lang_ver)
      var dd_tr_json = TransEngine.json_decode_translations();
      console.log(dd_tr_json)
      if(dd_tr_json == undefined || dd_tr_json == null || dd_tr_json == '' ||
         dd_tr_json['translations'] == undefined ||
         dd_tr_json['translations'][lang_ver] == undefined) {
          return;
      }
      $("#id_quote_textarea").val(dd_tr_json['translations'][lang_ver]['text']);
      $("#id_trans_footer").html("Last modified version: " + dd_tr_json['translations'][lang_ver]['footer']);
  },

  clear_dd_translations: function() {
      if (!confirm("Are you sure you want to erase all data? All content will be lost.")) {
          return false;
      }

      $("#id_current_translations").val("");
      $("#id_quote_textarea").val("");
      $("#dd_tr_translate").show();
      $("#dd_tr_translations").hide();
      $.ajax({
          type: "POST",
          url: url_clear_dd,
          data: [
              {"name": "quote_id", "value": quote_id},
          ],
          success: function(data) {
              $("#id_current_translations").val(JSON.stringify(data['data']));
              $("#id_quote_textarea").val("");
          },
          error: function(data){
              console.warn(data);
          }
      });
  },

  restore_dd_translations: function(init_orig_lang) {
      var dd_tr_json = TransEngine.json_decode_translations();
      console.log(dd_tr_json)
      if(dd_tr_json == undefined || dd_tr_json == null || dd_tr_json == '') {
          return;
      }

      for(var i in dd_tr_json['translations']) {
          TransEngine.dd_tr_modified[i] = false;
      }

      if(init_orig_lang &&
          dd_tr_json['orig_lang'] != undefined &&
          dd_tr_json['orig_lang'] != null &&
          dd_tr_json['orig_lang'] != ''
      ) {
          $("#id_selected_language").val(dd_tr_json['orig_lang']);
      }
      $("#dd_tr_translate").hide();
      $("#dd_tr_translations").show();
      $("#id_selected_language").unbind('change');
      $("#id_selected_language").change(TransEngine.show_lang_version);
    //   $("#id_selected_language").trigger('change');
  },

  handle_translate_dd: function() {
      var orig_lang = $("#id_original_language").val();
      var contents = TransEngine.get_current_contents();
      if(orig_lang == undefined || orig_lang == null || orig_lang == '') {
          alert("Please select original language");
          return;
      }
      $("#tr-loading").modal();

      $.ajax({
          type: "POST",
  //            dataType: "html",
  //            contentType: "json",
          url: url_translate_dd,
          data: [
              {"name": "quote_id", "value": quote_id},
              {"name": "contents", "value": contents},
              {"name": "orig_lang", "value": orig_lang}
          ],
          success: function(data) {
              if(data['status'] == 'OK') {

                  var dd_tr_json = JSON.stringify(data['data']);
                  $("#id_current_translations").val(dd_tr_json);
                  TransEngine.restore_dd_translations(true);
                  $("#tr-loading").modal("hide");
              }
          },
          error: function(data){
              console.warn(data);
              $("#tr-loading").modal("hide");
              alert(data.responseJSON.data);
          }
      });
  }

};

init.push(function () {
  $("#btn_trans").unbind("click");
  $("#btn_trans_update").unbind("click");

  $("#btn_trans").click(function() {
      TransEngine.handle_translate_dd();
      return false;
  })
  TransEngine.restore_dd_translations(true);
});

init.push(function () {
    pdg_widget = new PDG_Widget({});
    pdg_widget.init();
    pdg_widget_language = new PDG_Widget1({});
    pdg_widget_language.init();
});

$(document).ready(function(){
    var all_places_by_ids = {};
    $('#id_connected_venue').select2({
        allowClear: true,
        width: '100%',
        placeholder: 'Select Connected Venue...',
        dropdownParent: $('#connected_venue_selector'),
        ajax: {
            // url: "/ajax/autocomplete/place/published/list",
            url: "/ajax/autocomplete/place/for-featured-venue?for_quote=true&exclude_id="+venue_id,
            dataType: 'json',
            delay: 250,
            processResults: function (data, params) {
                for (var i in data.items){
                    var item0 = data.items[i];
                    all_places_by_ids[item0.id] = item0;
                }
                params.page = params.page || 1;
                return {
                    results: $.map(data.items, function(item){
                        if (item.name){
                            item.text =  item.name + ", " + item.street_address + item.zip_code + item.city + item.country + item.type;
                            return item;
                        }
                    }),
                };
            },
        },
        cache: true,
    });

    $('#id_connected_venue').change(function(){
        $(".venueAction").removeClass("d-none")
    })

    $('#id_selected_venue').select2({
        allowClear: true,
        width: '100%',
        placeholder: 'Select a venue and its Quote',
        dropdownParent: $('#selected_venue_selector'),
        ajax: {
            url: "/ajax/autocomplete/place/for-featured-venue?for_quote_8_list=true",
            dataType: 'json',
            delay: 250,
            processResults: function (data, params) {
                for (var i in data.items){
                    var item0 = data.items[i];
                    all_places_by_ids[item0.id] = item0;
                }
                params.page = params.page || 1;
                return {
                    results: $.map(data.items, function(item){
                        if (item.name){
                            item.text =  item.name + ", " + item.street_address + item.zip_code + item.city + item.country + item.type;
                            return item;
                        }
                    }),
                };
            },
        },
        cache: true,
    });

    function getQuoteList(data){
        var quoteList = "";
        for (i = 0; i < data.length; i++){
                quoteList += '<div class="task" data-title="'+ data[i].id+'" id="task'+ data[i].id+'">' +
                                '<div class="fa fa-arrows-v task-sort-icon"></div>' +
                                '<div class="action-checkbox">'+
                                    '<input type="checkbox" class="featred_quote_item" id="todo'+ data[i].id+'" name="featred_quote_item" value="'+ data[i].id+'">'+
                                    '<label for="todo'+ data[i].id+'" class="task-title">'+ data[i].text+  '</label>'+
                                '</div>'+
                            '</div>';
        }
        $("#sortable-list").html(quoteList);
    }
    $('#btnDelFeaturedQuote').click(function(){
        if (confirm("Do you really want to delete selected quote?")) {
            $(".loader").css("display","flex");
            var selected = new Array();
            $('.featred_quote_item:checked').each(function() {
                selected.push(this.value);
            });
            $.ajax({
                type: "POST",
                url: "/quote/remove-featured-quotes/",
                data: {  ids: JSON.stringify(selected) },
                dataType: 'json',
                success: function(data){
                    $(".loader").css("display","none");
                    getQuoteList(data.data)
                },
                dataType: "json"
            });
        }
        return false;
    })
    var list = $('#sortable-list');
    var fnSubmit = function(){
        var sortId = [];
        list.children('.task').each(function(){
            sortId.push($(this).data('title'));
        });
        $.ajax({
            type: "POST",
            url: "/quote/change-featured-quote-order/",
            data: {  ids: JSON.stringify(sortId) },
            dataType: 'json',
            success: function(data){
                getQuoteList(data.data)
            },
            dataType: "json"
        });
    };
    list.sortable({
        opacity: 0.9,
        update: function() {
            fnSubmit(); 
        }
    });
    $('#btnAdd').click(function(){
        $(".loader").css("display","flex");
        $.ajax({
            type: "POST",
            url: "/quote/add-featured/"+$("#id_selected_venue").val()+'/',
            data: {},
            success: function(response){
                $(".loader").css("display","none");
                getQuoteList(response.data);
                $('#id_selected_venue').val(null).trigger('change');
            },
            dataType: "json"
        });
    })
    $("#datetimepicker1").flatpickr({
      enableTime: true,
      dateFormat: "Y-m-d H:i",
    });

    $("#datetimepicker2").flatpickr({
      enableTime: true,
      dateFormat: "Y-m-d H:i",
    });

    $('#id_image_').on('change', function() {

      if (this.files[0].size > max_upload_size * 1000){
        if ($('.errorlist:contains("axim")').length < 2){
          $('#image_error_list').removeAttr('hidden');
        }
      } else {
        $('.errorlist:contains("axim")').attr('hidden', true);
      }

    });
});