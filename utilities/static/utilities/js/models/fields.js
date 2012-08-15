if(typeof String.prototype.trim !== 'function') {
  String.prototype.trim = function() {
    return this.replace(/^\s+|\s+$/g, ''); 
  }
}


var $class = function(def) {
    var constructor = def.hasOwnProperty('constructor') ? def.constructor : function() { };
    for (var name in $class.Initializers) {
        $class.Initializers[name].call(constructor, def[name], def);
    }
    return constructor;
};

$class.Initializers = {
    Extends: function(parent) {
        if (parent) {
            var F = function() { };
            this._superClass = F.prototype = parent.prototype;
            this.prototype = new F;
        }
    },

    Mixins: function(mixins, def) {
        this.mixin = function(mixin) {
            for (var key in mixin) {
                if (key in $class.Initializers) continue;
                this.prototype[key] = mixin[key];
            }
            this.prototype.constructor = this;
        };
        var objects = [def].concat(mixins || []);
        for (var i = 0, l = objects.length; i < l; i++) {
            this.mixin(objects[i]);
        }
    }
};

var Validator = $class({

    constructor: function(el) {
    	this.el = el;
    	this.color = el.css("color");
    	this.load(el);
    },

    load: function(el){

    },
    
    keypress: function() {
        
    },
    
    focus: function() {
    	this.el.css("color", this.color);
    },
    
    blur: function() {
    	if (!this.isValid(this.el.val())) {
    		this.el.css("color", "red");
    	} else {
    		this.el.val(this.style(this.el.val()));
    	}
    },
    
    isValid: function(val) {
    	return true;
    },
    
    style: function(val) {
    	return val;
    }

});


var PhoneValidator = $class({

    Extends: Validator,

    constructor: function(el) {
    	Validator.call(this, el);
    },
    
    load: function(el){
    	if (el.val() == "" || el.val().trim()=="+420") {
			el.val("+420");
			el.css("color","#bbbbbb");
		} else blur();
    },
    
    isValid: function(val) {
    	return (val.match(/^(\+?\d{3})? *(\d{3}) *(\d{3}) *(\d{3})$/) != null);
    },

    style: function(val) {
    	var result=val.match(/^(\+?\d{3})? *(\d{3}) *(\d{3}) *(\d{3})$/); 
   		if (result[1] == undefined) {
    		result[1] = "+420";
    	} else if(result[1].charAt(0) != "+"){
    		result[1] = "+"+result[1];
    	}
    	return result[1]+" "+result[2]+" "+result[3]+" "+result[4];
    }
});


var PscValidator = $class({

    Extends: Validator,

    constructor: function(el) {
    	Validator.call(this, el);
    },
    
    isValid: function(val) {
    	return (val.match(/^(\d{3}) *(\d{2})$/) != null);
    },

    style: function(val) {
    	var result=val.match(/^(\d{3}) *(\d{2})$/); 
		return result[1]+" "+result[2];
    }
});

function showPopup(triggeringLink) {
    var name = triggeringLink.id;
    href = triggeringLink.href;
    var win = window.open(href, name, 'height=500,width=1200,resizable=yes,scrollbars=yes');
    win.focus();
    return false;
}


sdiak="ÁÂÄĄáâäąČčĆćÇçĈĉĎĐďđÉÉĚËĒĖĘéěëēėęĜĝĞğĠġĢģĤĥĦħÍÎíîĨĩĪīĬĭĮįİıĴĵĶķĸĹĺĻļĿŀŁłĹĽĺľŇŃŅŊŋņňńŉÓÖÔŐØŌōóöőôøŘřŔŕŖŗŠšŚśŜŝŞşŢţŤťŦŧŨũŪūŬŭŮůŰűÚÜúüűŲųŴŵÝYŶŷýyŽžŹźŻżß ";
bdiak="AAAAaaaaCcCcCcCcDDddEEEEEEEeeeeeeGgGgGgGgHhHhIIiiIiIiIiIiIiJjKkkLlLlLlLlLLllNNNNnnnnnOOOOOOooooooRrRrRrSsSsSsSsTtTtTtUuUuUuUuUuUUuuuUuWwYYYyyyZzZzZzs-";


function pageUrl() {
	$('input.page-url').each(function(){
		elUrl = $(this);
		canChange = elUrl.val() == "";
		startVal = elUrl.val();
		elUrl.focus(function() {
			startVal = elUrl.val();
		});
		elUrl.blur(function() {
			canChange = (elUrl.val() == "") || (startVal == elUrl.val() && canChange);
		});
    });
	
	$('input.page-title').each(function(){
		el = $(this);
		el.keyup(function(objEvent){
			input = el.val();
			output = "";
			for(p=0;p<input.length;p++)
			{
				if (sdiak.indexOf(input.charAt(p)) !=-1 )	output += bdiak.charAt(sdiak.indexOf(input.charAt(p)));
				else output+=input.charAt(p);
			}
			if (canChange && $('input.page-url').parent().parent().css('display') != 'none')	$('input.page-url').val(output);
		});
    });
}


function hideFields(){
	$(".hide").each( function() {
		var el = $(this);
		
		var hideF = function(){
			var hide_relations = el.attr('class').split(" ");
			for (var i = 1; i<hide_relations.length;i++) {
				hide_relation = hide_relations[i].split('-');
				if((hide_relation[0] == 'unchecked' && el.is(':checked')) || (hide_relation[0] == 'checked' && !el.is(':checked')) ){
		            $('.'+hide_relation[1]).css('display','none');
				} else {
		            $('.'+hide_relation[1]).css('display','block');
				}
			
			}
		};
		
		el.click(hideF);
		hideF();
	});
	
	$(".select-hide").each( function() {
		var el = $(this);
		
		var hideSelectF = function(){
			var hide_relations = el.attr('class').split(" ")
			for (var i = 1; i<hide_relations.length;i++) {
				hide_relation = hide_relations[i].split('-');
				if(el.val() == hide_relation[0] && hide_relation[1] == 'set'){
			        $('.'+hide_relation[2]).css('display','block');
				} else if(el.val() != hide_relation[0] && hide_relation[1] == 'notset'){
					$('.'+hide_relation[2]).css('display','block');
				} else {
					$('.'+hide_relation[2]).css('display','none');
					if ($('.'+hide_relation[2]+' select').length != 0) {
						$('.'+hide_relation[2]+" option:selected").removeAttr("selected");
						$('.'+hide_relation[2]+" select").each(function() { 
							$(this).find("option:first").attr("selected", "selected");
  						
						});
	
					}					
					$('.'+hide_relation[2]+ ' input').val('');
				}
				
			}
		};
		el.change(hideSelectF);
		hideSelectF();
	});

}


function otherSelectFields() {
	$(".other-select").each( function() {
		var select = $(this);
		var otherSelectFunc = function() {
			if (select.val() == '__other__') {
				select.parent().find('input[type=text]').css('display', 'inline');
			} else {
				select.parent().find('input[type=text]').css('display', 'none');
			}
		}
		select.change(otherSelectFunc);
		otherSelectFunc();
	});
}

validators = {"CZ-phone":PhoneValidator,"psc":PscValidator}


function styleIntegerInput(el) {
	val = el.val().split(' ').join('').replace(/^[0]+(\d)/g,"$1").replace(/[^\d]/g, "");	
	out = ''
	j = 0;
	for (i=val.length - 1; i>=0;i--){
		if (j % 3 == 0){
			out = ' '+out
		}
		out = val.charAt(i) + out;		
		j++;
	}
	el.val(out.trim());
}

function autoFormatInteger() {
	$('input.integer.auto-format').each(function(){
        styleIntegerInput($(this));
		$(this).keyup(function(objEvent){
			styleIntegerInput($(this));
		});
	});
	
}

$(document).ready(function(){
		//phone();
		pageUrl();
		//psc();
		
		hideFields();
		otherSelectFields();
		autoFormatInteger();
		/*$("#id_is_dynamic").click(
				function(){hideHTML()}
		);  */
		
		for(var key in validators)
	    {
			$('input.'+key).each(function(){
				el = $(this);
				var validator = new (validators[key])($(this));
				el.focus(function() {
					validator.focus();
		    	});
		    	el.blur(function() {
		    		validator.blur();
		    	});
		    });

	    }
});

