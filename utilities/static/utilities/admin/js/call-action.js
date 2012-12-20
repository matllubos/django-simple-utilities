function call_action(action,object) {
	var csrfmiddlewaretokenInput=document.getElementsByName("csrfmiddlewaretoken");
	data = [
		{'name':'csrfmiddlewaretoken','id':'csrfmiddlewaretoken','value':csrfmiddlewaretokenInput[0].value},
		{'name':'action','id':'action','value':action},
		{'name':'_selected_action','id':'_selected_action','value':object},	
	]
	
	var form = document.createElement("form");
	form.setAttribute("method", "post");
	form.setAttribute("action", '');
	
	for (field_id in data)
	{
	    var field = document.createElement("input");
	    field.setAttribute("type", "hidden");
	    field.setAttribute("id", data[field_id]['id']);
	    field.setAttribute("name", data[field_id]['name']);
	    field.setAttribute("value", data[field_id]['value']);
	    form.appendChild(field);
	}	
	document.body.appendChild(form);
	form.submit();
}