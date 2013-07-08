jQuery(function($) {
      $('input.datetimepicker').datepicker(
      {
        duration: '',
        changeMonth: false,
        changeYear: false,
        yearRange: '1900:2060',
        showTime: false,
        time24h: true
      });

    $.datepicker.regional['cs'] = {
        closeText: 'Zavřít',
        prevText: '&#x3c;Dříve',
        nextText: 'Později&#x3e;',
        currentText: 'Nyní',
        monthNames: ['leden', 'únor', 'březen', 'duben', 'květen', 'červen', 'červenec', 'srpen',
            'září', 'říjen', 'listopad', 'prosinec'],
        monthNamesShort: ['led', 'úno', 'bře', 'dub', 'kvě', 'čer', 'čvc', 'srp', 'zář', 'říj', 'lis', 'pro'],
        dayNames: ['neděle', 'pondělí', 'úterý', 'středa', 'čtvrtek', 'pátek', 'sobota'],
        dayNamesShort: ['ne', 'po', 'út', 'st', 'čt', 'pá', 'so'],
        dayNamesMin: ['ne', 'po', 'út', 'st', 'čt', 'pá', 'so'],
        weekHeader: 'Týd',
        dateFormat: 'dd.mm.yy',
        firstDay: 1,
        isRTL: false,
        showMonthAfterYear: false,
        yearSuffix: ''
    };
    $.datepicker.setDefaults($.datepicker.regional['cs']);
});

/* Czech translation for the jQuery Timepicker Addon */
/* Written by Ondřej Vodáček */
(function($) {
	$.timepicker.regional['cs'] = {
		timeOnlyTitle: 'Vyberte čas',
		timeText: 'Čas',
		hourText: 'Hodiny',
		minuteText: 'Minuty',
		secondText: 'Vteřiny',
		millisecText: 'Milisekundy',
		timezoneText: 'Časové pásmo',
		currentText: 'Nyní',
		closeText: 'Zavřít',
		timeFormat: 'HH:mm',
		amNames: ['dop.', 'AM', 'A'],
		pmNames: ['odp.', 'PM', 'P'],
		isRTL: false
	};
	$.timepicker.setDefaults($.timepicker.regional['cs']);
})(jQuery);

$(document).ready(function(){
	$('.datepicker-widget').datepicker({
			  changeMonth: true,
		      changeYear: true,
		      yearRange: '1900:2060',
	});
	$('.datetimepicker-widget').datetimepicker({
			changeMonth: true,
		    changeYear: true
	});
});