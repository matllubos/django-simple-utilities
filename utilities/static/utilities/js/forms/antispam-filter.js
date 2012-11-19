$(document).ready(function($) {
	$(".antispam").each(function(){
		var el = $(this);
		el.val("2");
		el.parent().css('display', 'none');
	});
});