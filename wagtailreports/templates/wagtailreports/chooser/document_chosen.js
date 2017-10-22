function(modal) {
    modal.respond('reportChosen', {{ report_json|safe }});
    modal.close();
}
