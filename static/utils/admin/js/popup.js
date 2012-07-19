function showPopup(triggeringLink) {
    var name = triggeringLink.id;
    name = id_to_windowname(name);
    href = triggeringLink.href
    var win = window.open(href, name, 'height=500,width=800,resizable=yes,scrollbars=yes');
    win.focus();
    return false;
}
