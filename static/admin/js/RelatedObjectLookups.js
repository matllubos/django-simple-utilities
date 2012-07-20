function dismissEditPopup(win, newId, newRepr) { 
	var name = win.name.replace(/___/g, '.'); 
 	var elem = document.getElementById(name); 
 	if(elem) { 
 		if( elem.nodeName == 'SELECT') { 
 			var o = new Option(newRepr, newId); 
 			elem.options[elem.selectedIndex] = o; 
 			o.selected = true; 
 		} 
 	} 
 	win.close(); 
	$('#'+name).change();
} 

function showEditAnotherPopup(triggeringLink) {
    var name = triggeringLink.id.replace(/^edit_/, '');
    name = id_to_windowname(name);
    href = triggeringLink.href
    if (href.indexOf('?') == -1) {
        href += '?_popup=1';
    } else {
        href  += '&_popup=1';
    }
    var win = window.open(href, name, 'height=500,width=800,resizable=yes,scrollbars=yes');
    win.focus();
    return false;
}

function showDeleteAnotherPopup(triggeringLink) {
    var name = triggeringLink.id.replace(/^delete_/, '');
    name = id_to_windowname(name);
    href = triggeringLink.href
    if (href.indexOf('?') == -1) {
        href += '?_popup=1';
    } else {
        href  += '&_popup=1';
    }
    var win = window.open(href, name, 'height=500,width=800,resizable=yes,scrollbars=yes');
    win.focus();
    return false;
}

function dismissAddAnotherPopup(win, newId, newRepr) {
    // newId and newRepr are expected to have previously been escaped by
    // django.utils.html.escape.
    newId = html_unescape(newId);
    newRepr = html_unescape(newRepr);
    var name = windowname_to_id(win.name);
    
    var elem = document.getElementById(name);
    if (elem) {
        if (elem.nodeName == 'SELECT') {
            var o = new Option(newRepr, newId);
            elem.options[elem.options.length] = o;
            o.selected = true;
        } else if (elem.nodeName == 'INPUT') {
            if (elem.className.indexOf('vManyToManyRawIdAdminField') != -1 && elem.value) {
                elem.value += ',' + newId;
            } else {
                elem.value = newId;
            }
        }
    } else {
        var toId = name + "_to";
        elem = document.getElementById(toId);
        var o = new Option(newRepr, newId);
        SelectBox.add_to_cache(toId, o);
        SelectBox.redisplay(toId);
    }
    win.close();

    $('#'+name).change();
}

function editSelectChange(el) {
	var edit = el.parent().find('.edit-another');
	if (el.val() == '') {
		edit.css('display', 'none');
	} else {
		edit.css('display', 'inline');
		edit.attr('href', edit.attr('href').replace(/[^\/]*\/$/, el.val()+'/'))
	}
}

function deleteSelectChange(el, val) {
	var deleteEl = el.parent().find('.delete-another');
	if (el.val() == '' || el.val() == val) {
		deleteEl.css('display', 'none');
	} else {
		deleteEl.css('display', 'inline');
		deleteEl.attr('href', deleteEl.attr('href').replace(/[^\/]*\/delete/, el.val()+'/delete'))
	}
}


function dismissDeletePopup(win, chosen) {
	for (var i=0; i<chosen.length; i++) {
    		//alert("."+chosen[i].app+"_"+chosen[i].model+" option[value='"+chosen[i].id+"']");
		$("."+chosen[i].app+"_"+chosen[i].model+" option[value='"+chosen[i].id+"']").remove();
		$("."+chosen[i].app+"_"+chosen[i].model).change();	
	}
	win.close();
	$('#'+name).change();
}



$(document).ready(function(){
	$('.edit-another').each(function() {
		var el =  $(this);
		var select = $(this).parent().find('select');
		editSelectChange(select);
		select.change(function(){
			editSelectChange($(this));
		});
	});

	$('.delete-another').each(function() {
		var el =  $(this);
		var select = $(this).parent().find('select');
		var val = select.val();
		deleteSelectChange(select, val);
		select.change(function(){
			deleteSelectChange($(this), val);
		});
	});
});
