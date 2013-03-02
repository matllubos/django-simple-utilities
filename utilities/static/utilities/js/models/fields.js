// Set caret position easily in jQuery
// Written by and Copyright of Luke Morton, 2011
// Licensed under MIT
(function ($) {
    // Behind the scenes method deals with browser
    // idiosyncrasies and such
    $.caretTo = function (el, index) {
        if (el.createTextRange) { 
            var range = el.createTextRange(); 
            range.move("character", index); 
            range.select(); 
        } else if (el.selectionStart != null) { 
            el.focus(); 
            el.setSelectionRange(index, index); 
        }
    };
    
    // Another behind the scenes that collects the
    // current caret position for an element
    
    // TODO: Get working with Opera
    $.caretPos = function (el) {
        if ("selection" in document) {
            var range = el.createTextRange();
            try {
                range.setEndPoint("EndToStart", document.selection.createRange());
            } catch (e) {
                // Catch IE failure here, return 0 like
                // other browsers
                return 0;
            }
            return range.text.length;
        } else if (el.selectionStart != null) {
            return el.selectionStart;
        }
    };

    // The following methods are queued under fx for more
    // flexibility when combining with $.fn.delay() and
    // jQuery effects.

    // Set caret to a particular index
    $.fn.caret = function (index, offset) {
        if (typeof(index) === "undefined") {
            return $.caretPos(this.get(0));
        }
        
        return this.queue(function (next) {
            if (isNaN(index)) {
                var i = $(this).val().indexOf(index);
                
                if (offset === true) {
                    i += index.length;
                } else if (typeof(offset) !== "undefined") {
                    i += offset;
                }
                
                $.caretTo(this, i);
            } else {
                $.caretTo(this, index);
            }
            
            next();
        });
    };

    // Set caret to beginning of an element
    $.fn.caretToStart = function () {
        return this.caret(0);
    };

    // Set caret to the end of an element
    $.fn.caretToEnd = function () {
        return this.queue(function (next) {
            $.caretTo(this, $(this).val().length);
            next();
        });
    };
}(jQuery));




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
    },
    
    beforeSubmit: function(val) {
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
    },
    
    beforeSubmit: function(val) {
    	if (val == "+420") return "";
    	return val;
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

var urlData = {}

function getOrder(el) {
	var order = el.attr('name').split('-');
	if (order.length == 3) return order[1];
	return '0';
}

function pageUrl() {
	$('input.page-url').each(function(){
		var elUrl = $(this);
		urlData[getOrder(elUrl)] =  {'canChange': elUrl.val() == "", 'startVal':elUrl.val() };
		elUrl.focus(function() {
			urlData[getOrder(elUrl)].startVal = elUrl.val();
		});
		elUrl.blur(function() {
			urlData[getOrder(elUrl)].canChange = (elUrl.val() == "") || (urlData[getOrder(elUrl)].startVal == elUrl.val() && urlData[getOrder(elUrl)].canChange);
		});
    });
	
	$('input.page-title').each(function(){
		var el = $(this);
		el.keyup(function(objEvent){
			var input = el.val();
			var output = "";
			for(p=0;p<input.length;p++)
			{
				if (sdiak.indexOf(input.charAt(p)) !=-1 )	output += bdiak.charAt(sdiak.indexOf(input.charAt(p)));
				else output+=input.charAt(p);
			}
			if (urlData[getOrder(el)].canChange && $('input.page-url').parent().parent().css('display') != 'none'){
				$('input.page-url').each(function(){
					if (getOrder(el) == getOrder($(this))) {
						$(this).val(output);
					}
				});
				
				
				
			}
		});
    });
}


function hideFields(){
	$(".checkbox-hide").each( function() {
		var el = $(this);
		
		var hideF = function(){
			var hide_fields = el.attr('class').split(" ");
			for (var i = 1; i<hide_fields.length;i++) {
								
				hide_field = hide_fields[i].split('--');
				if((hide_field[0] == 'unchecked' && el.is(':checked')) || (hide_field[0] == 'checked' && !el.is(':checked')) ){
		            $('.field-'+hide_field[1]).css('display','none');
				} else {
		            $('.field-'+hide_field[1]).css('display','block');
				}
			
			}
		};
		
		el.click(hideF);
		hideF();
	});
	
	$(".select-hide").each( function() {
		var el = $(this);
		
		var hideSelectF = function(){
			if (el.val() == null) return;
			
			var hide_relations = el.attr('class').split(" ")
			
			var show_relations = [];
			
			for (var i = 1; i<hide_relations.length;i++) {
				hide_relation = hide_relations[i].split('--');
				
				var val = hide_relation[0].split('__').join(' ')
				var className = hide_relation[2];
				
				if(el.val() == val && hide_relation[1] == 'set'){
					show_relations[className] = true;
				} else if(el.val() == val && hide_relation[1] == 'notset'){
					show_relations[className] = false;
				} else if (show_relations[className] == undefined){
					show_relations[className] = hide_relation[1] != 'set';
				}
				
			}

			for(var className in show_relations) {
			    if (show_relations[className]) {
			    	$('.field-'+className).show();
			    } else {
			    	$('.field-'+className).hide();
					if ($('.field-'+className+' select').length != 0) {
						$('.field-'+className+" option:selected").removeAttr("selected");
						$('.field-'+className+" select").each(function() { 
							$(this).find("option:first").attr("selected", "selected");
  						
						});
	
					}					
					$('.field-'+className+ ' input').val('');
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
				select.parent().find('input[type=text]').css('display', 'inline').addClass('open');
				select.addClass('open');
			} else {
				select.parent().find('input[type=text]').css('display', 'none').removeClass('open');
				select.removeClass('open');
			}
		}
		select.change(otherSelectFunc);
		otherSelectFunc();
	});
}

validators = {"CZ-phone":PhoneValidator,"psc":PscValidator}


function styleIntegerInput(el) {
	var position = 0;
	var focus = false;
	if (el.is(":focus")){
		var position = el.caret();
		focus=true;
	}
	var val = el.val();
	var stylizedValue = "";
	var stylizedPosition = position;
	var firstZero = true;
	for (i=0; i<val.length;i++) {
		if (!/^\d$/.test(val.charAt(i)) || (val.length != 1 && val.charAt(i) == '0' && firstZero)) {
			if (i < position){
				stylizedPosition--;
			}
		} else {
			stylizedValue += val.charAt(i);
			firstZero = false;
		}
	}
	
	out = ''
	j = 0;
	for (i=stylizedValue.length - 1; i>=0;i--){
		if (j % 3 == 0 && j != 0){
			out = ' '+out
			if (i + 1 <= stylizedPosition) {
				stylizedPosition++;
			}
		}
		out = stylizedValue.charAt(i) + out;		
		j++;
	}

	if (val != out.trim()){
		el.val(out.trim());
		if (focus){
			el.caret(stylizedPosition);
		}
	}
}

function autoFormatInteger() {
	$('input.integer.auto-format').each(function(){
        styleIntegerInput($(this));
		$(this).keyup(function(objEvent){
			styleIntegerInput($(this));
		});
	});
	
}


forms = {}

function addBeforeSubmitAction(form, action) {
	if(forms[form] == undefined) {
		forms[form] = [];
		var submitForm = false;
		form.submit(function() {
			if(!submitForm){
				form = $(this);
				for (key in forms[form]) {
					forms[form][key]();
				}
				submitForm = true;
				form.submit();
				return false;
			}
			return true;
		});
	}
	
	forms[form].push(action);

	
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
				var el = $(this);
				var validator = new (validators[key])($(this));
				el.focus(function() {
					validator.focus();
		    	});
		    	el.blur(function() {
		    		validator.blur();
		    	});
		    	addBeforeSubmitAction(el.parents('form'), function(){
		    		val = el.val();
		    		beforeSubmitVal = validator.beforeSubmit(val);
		    		if (val != beforeSubmitVal) {
		    			el.val(beforeSubmitVal);
		    		}
		    	});	    	
		    });

	    }
});

