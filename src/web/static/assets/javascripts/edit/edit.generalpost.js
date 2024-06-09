var pdg_widget = null;

function loadRelatedLists(){
    loadAndInsertHtmlByAjax(ajax_related_lists_url, "related_lists");
}

init.push(function () {
    if (!is_new) {
        loadRelatedLists();
    }
});

init.push(function () {
    pdg_widget = new PDG_Widget({});
    pdg_widget.init();
});
