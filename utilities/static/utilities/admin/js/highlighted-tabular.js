function prepareHighlighted(id) {
	var el = $('#'+id)
	
	var background = el.css('background');
	var focus = false;
	el.hover(function(){el.css('background','#f0ff9b')}, function(){if (!focus) el.css('background',background);});
	el.find('input,textbox,select').bind('focus', function(){
		el.css('background','#f0ff9b');
		focus=true;
	});
	
	el.find('input,textbox,select').bind('blur',function(){
		el.css('background',background);
		focus=false;
	});
	 
	
	el.find('input,textbox,select').keydown(function(event) {
		if (event.altKey){
			switch(event.keyCode) {
				case 40:
					className = $(this).parents('td').attr('class');
					if (el.next('tr.highlighted:not(.empty-form)').length == 0) django.jQuery(".add-row a").trigger('click');
					el.next('tr.highlighted:not(.empty-form)').find('td.'+className).find('input,select,textbox').focus();
					break;
				case 38:
					className = $(this).parents('td').attr('class');
					el.prev('tr.highlighted').find('td.'+className).find('input,select,textbox').focus();
					break;
				case 39:
					$(this).parents('td').next('td').find('input,select,textbox').focus();
					el.css('background','#f0ff9b');
					break;
				case 37:
					$(this).parents('td').prev('td').find('input,select,textbox').focus();
					el.css('background','#f0ff9b');
					break;
			}
			
			
		}
	});
	
}




$(document).ready(function(){
	$('tr.highlighted').each(function(){
		var el = $(this);
		prepareHighlighted(el.attr('id'));
	});

});