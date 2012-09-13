$(document).ready(function(){
	$('tr.highlighted').each(function(){
		var el = $(this);
		var background = el.css('background');
		var focus = false;
		$(this).hover(function(){el.css('background','#f0ff9b')}, function(){if (!focus) el.css('background',background);});
		$(this).find('input,textbox,select').focus(function(){el.css('background','#f0ff9b');focus=true;});
		$(this).find('input,textbox,select').blur(function(){el.css('background',background);focus=false;});
		 
		
		$(this).find('input,textbox,select').keydown(function(event) {
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
	});

});