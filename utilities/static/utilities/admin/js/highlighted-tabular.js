function highlight(obj) {
	var el = $(obj);
	var background = el.css('background');
	var focus = false;
	el.hover(function(){el.css('background','#f0ff9b')}, function(){if (!focus) el.css('background',background);});
	el.find('input,textbox,select').focus(function(){el.css('background','#f0ff9b');focus=true;});
	el.find('input,textbox,select').blur(function(){el.css('background',background);focus=false;});
	 
	
	el.find('input,textbox,select').keydown(function(event) {
		if (event.altKey){
			switch(event.keyCode) {
				case 40:
					className = $(this).parents('td').attr('class');
					el.next('tr.highlighted').find('td.'+className).find('input,select,textbox').focus();
					break;
				case 38:
					className = $(this).parents('td').attr('class');
					el.prev('tr.highlighted').find('td.'+className).find('input,select,textbox').focus();
					break;
				case 39:
					if ($(this).parents('td').next('td:not(.delete)').length !=0 ) {
						$(this).parents('td').next('td').find('input,select,textbox').focus();
						el.css('background','#f0ff9b');
					} else {
						el.next('tr.highlighted').find('td:not(.original):first').find('input,select,textbox').focus();
					}
					break;
				case 37:
					if ($(this).parents('td').prev('td:not(.original)').length !=0 ) {
						$(this).parents('td').prev('td').find('input,select,textbox').focus();
						el.css('background','#f0ff9b');
					} else {
						el.prev('tr.highlighted').find('td:not(.delete):last').find('input,select,textbox').focus();
					}
					break;
			}
			
			
		}
	});
}


$(document).ready(function(){
	$('tr.highlighted').each(function(){
		highlight(this);
	});

});