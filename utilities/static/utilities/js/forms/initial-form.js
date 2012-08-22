$(document).ready(function($) {
	$('input.initial[type=text],input.initial[type=email],textarea.initial').click(function() {
		if ($(this).val() == $(this).attr("title")) $(this).val('');
	});
	$('input.initial[type=text],input.initial[type=email],textarea.initial').blur(function() {
		var el = $(this);
		if (el.val() == '') el.val(el.attr("title"));
	});
});