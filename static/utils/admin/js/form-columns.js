var columns = new Array();


var columnsGroups = new Array();
var parentWidth;
var windowWidth;

function loadColumns() {
	maxHeight = 0;
	
	var columnsGroup = new Array();
	$('fieldset.columns').parent().children('fieldset').each(function(){
		fieldset = $(this);
		if (fieldset.hasClass('columns')) {
			var height = fieldset.height() + fieldset.find("p.help").length * 30;
			fieldset.find("p.help").css('display', 'none');
			columnsGroup.push({height: height, width: fieldset.width(), column: fieldset});
			fieldset.find("p.help").css('display', 'block');
		} else if(columnsGroup.length != 0) {
			columnsGroups.push(columnsGroup);
			columnsGroup = new Array();
		}
	});

	/*
	$("p.help").css('display', 'none');
	
	$(".columns").each(function(){
		column = $(this);
		columns.push({height: column.height(), width: column.width(), column: column});
	});
	*/
}


function getRows(width) {
	var rows = new Array();
	var rowColumns = new Array();
	rows.push(rowColumns);
	
	var currentWidth = 0;
	$.each(columns, function(){
		column = this;
		currentWidth += column.width + 5;
		if (currentWidth != column.width && currentWidth > width) {
			rowColumns = new Array();
			rows.push(rowColumns);
			currentWidth = 0;
		}
		rowColumns.push(column);
	});
	return rows;
}


function getRows2(width) {
	var rows = new Array();
	
	
	$.each(columnsGroups, function(){
		columnsGroup = this;
		
		var rowColumns = new Array();
		rows.push(rowColumns);
		var currentWidth = 0;
		
		$.each(columnsGroup, function(){
			column = this;
			currentWidth += column.width;
			if (currentWidth != column.width && currentWidth > width) {
				rowColumns = new Array();
				rows.push(rowColumns);
				currentWidth = 0;
			}
			rowColumns.push(column);
		});
	});
	return rows;
}


function getRows3(width) {
	var rows = new Array();
	
	
	$.each(columnsGroups, function(){
		columnsGroup = this;
		
		var rowColumns = new Array();
		rows.push(rowColumns);
		var currentWidth = 0;
		
		var i = 0;
		var max = columnsGroup.length;
		var penultimate = null;
		$.each(columnsGroup, function(){
			column = this;
			currentWidth += column.width;
			
		
			if (currentWidth != column.width && currentWidth > width) {
				rowColumns = new Array();
				rows.push(rowColumns);
				currentWidth = 0;
			}
			
			if (i != max - 2 || max <= 3) {
				if (penultimate != null) {
					rowColumns.push(penultimate);
				}
				rowColumns.push(column);
			} else {
				penultimate = column;
			}

			i++;
		});
	});
	return rows;
}



function alignColumns(rows, pwidth) {
	$.each(rows, function(){
		var rowColumns = this;
		var maxHeight = 0;
		var maxWidth = 0;
		$.each(rowColumns, function(){
			column = this;
			if (maxHeight < column.height){
				maxHeight = column.height;
			}
			maxWidth += column.width;
		});
		var i = 0;
		$.each(rowColumns, function(){
			$(this.column).css("min-height",maxHeight+"px");
			var width = this.width - 7 + (pwidth - maxWidth) / rowColumns.length;
			
			if (++i == rowColumns.length) {
				width += 5;
				$(this.column).css("margin-right", "0");
			} else {
				$(this.column).css("margin-right", "5px");
			}
			$(this.column).css("width",width+"px");
		});
	});
}

$(document).ready(function(){
	windowWidth = $(window).width();
	parentWidth = $('fieldset.columns').parent().width();
	if (windowWidth < 930 ) windowWidth = 930;
	loadColumns();
	alignColumns(getRows3(parentWidth), parentWidth);
});

$(window).resize (function(){
	width = parentWidth + $(window).width() - windowWidth;
	
	if (width < 900 ) width = 900;
	alignColumns(getRows3(width), width);
	//alert("měním");


	});
