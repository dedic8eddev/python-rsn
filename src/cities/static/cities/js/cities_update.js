$(document).ready(function (){
    $('#draft_version').on('click', function (e) {
        e.preventDefault();
        $('#published_flag').prop('checked', false)
        $('#geo_form').submit()
    })

    $('#publish_version').on('click', function (e) {
        e.preventDefault();
        $('#published_flag').prop('checked', true)
        $('#geo_form').submit()
    })
    $('.limit-input').unbind('keyup change input paste').bind('keyup change input paste', function(e){
        var $this = $(this);
        var val = $this.val();
        var valLength = val.length;
        var maxCount = $this.attr('maxlength');
        counter = $(this).data('counter')
        lefter = $(this).data('left')

        // localStorage.setItem(counter,valLength)
        // localStorage.setItem(lefter,maxCount-valLength)

        $('#'+counter).text(valLength)
        $('#'+lefter).text(maxCount-valLength)
        if(valLength>maxCount){
            $this.val($this.val().substring(0,maxCount));
        }
    });
    var limit1 = $(".title_field").attr("maxlength");
    var limit2 = $(".description_field").attr("maxlength");

    if (!$(".description_field").val()) {
        $("#myCounter2").text("0")
        $("#left_limit2").text(limit2)
    }
    else{
        $("#left_limit2").text(limit2 - $(".description_field").val().length)
        $("#myCounter2").text($(".description_field").val().length)
    }


    if (!$(".title_field").val()) {
        $("#myCounter1").text("0")
        $("#left_limit1").text(limit1)
    }
    else{
        $("#left_limit1").text(limit1 - $(".title_field").val().length)
        $("#myCounter1").text($(".title_field").val().length)
    }
})