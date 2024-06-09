app.ready(function () {
    $("#submit").click(function (e) {
        let policyAgreement = $("#terms")[0].checked;
        let policyLabel = $("#terms-label");

        if (!policyAgreement) {
            policyLabel.css("color", "red");
            e.preventDefault()
        } else policyLabel.css("color", "#757575");
    });

    $("#terms").change(function () {
        console.log($(this))
       if(this.checked) $("#terms-label").css("color", "#757575");
    })
});