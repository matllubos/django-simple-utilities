(function() {
    
    // walk the editors dom and insert special chars 
    // or revert what was done before depending on toggle_mode
    function toggleContents(node, toggle_mode) {

        for (var i=0; i<node.childNodes.length; i++) {
            el = node.childNodes[i];
            if (el.nodeType == 3) { 
                if (toggle_mode) {
                    el.nodeValue = el.nodeValue.replace(/\u00b7\u200b/g, ' ');
                }
                else {
                    el.nodeValue = el.nodeValue.replace(/\ /g, '\u00b7\u200b');
                }
            }
            else if (el.nodeName.toLowerCase() == 'br'){
                //console.log("br found");
                var bogus = el.hasAttribute ? el.hasAttribute('_mce_bogus') : el.getAttribute('_mce_bogus');
                if (!toggle_mode && !bogus) { // \u21B5
                    el.parentNode.insertBefore(document.createTextNode('\u21B5'),el);
                    i++;
                }
                else {
                    sibling = el.previousSibling;
                    if (sibling && sibling.nodeType == 3) sibling.nodeValue = sibling.nodeValue.replace(/\u21B5/g, '');
                }
            }
            else if (el.nodeName.toLowerCase() == 'p'){
                //console.log("p found");
                
                if (!toggle_mode) { // \u00b6
                    chr = '\u00b6';
                    el.appendChild(document.createTextNode(chr));
                }
                else {
                    if(el.lastChild && el.lastChild.nodeType == 3) el.lastChild.nodeValue = el.lastChild.nodeValue.replace(/\u00b6/g, '');
                }
            }
            if (el.childNodes.length > 0) { toggleContents(el, toggle_mode); }
        }
        return 1;
    }
                
    tinymce.create('tinymce.plugins.hiddenchars', {
        
        init : function(ed, url) {

            // Register hiddenchars button
            ed.addButton('hiddenchars', {
                title : 'Toggle hidden characters',
                cmd : 'mce_toggle_hidden_chars',
            });
            
            ed.onInit.add(function(ed) {
                ed.hiddenchars_toggled = false;
            });
            
            function toggleback(ed){
                if (ed.hiddenchars_toggled) {
                    var root = ed.getBody();
                    toggleContents(root, true);
                    ed.hiddenchars_toggled = false;
                    ed.controlManager.setActive('hiddenchars', ed.hiddenchars_toggled);
                }
            };
            
            ed.onKeyDown.add(function(ed) {
                toggleback(ed);
            });
            
            ed.onClick.add(function(ed){
                toggleback(ed);
            });
            
            
            ed.addCommand('mce_toggle_hidden_chars', function() {
                var root = ed.getBody();
                toggleContents(root,ed.hiddenchars_toggled);
                
                                
                ed.hiddenchars_toggled = !ed.hiddenchars_toggled;
                ed.controlManager.setActive('hiddenchars', ed.hiddenchars_toggled);

            });
        },
    });
    // Register plugin
    tinymce.PluginManager.add('hiddenchars', tinymce.plugins.hiddenchars);

})();




tinyMCE.init({
	mode : "specific_textareas",
    editor_selector : /(tinymce)/,
  	entity_encoding : "raw",
	theme : "advanced",
	theme_advanced_toolbar_location : "top",
	theme_advanced_toolbar_align : "left",
	theme_advanced_statusbar_location : 'bottom', 
	theme_advanced_path : false, 
	theme_advanced_resizing : true, 
	theme_advanced_resizing_use_cookie : true,
	theme_advanced_buttons1 : "fullscreen,removeformat,separator,preview,separator,bold,italic,underline,strikethrough,separator,bullist,numlist,outdent,indent,separator,undo,redo,separator,link,unlink,anchor,separator,image,media,cleanup,help,code,hiddenchars",
	theme_advanced_buttons2 : "",
	theme_advanced_buttons3 : "",
	auto_cleanup_word : true,
	plugins : "fullscreen, tabfocus, hiddenchars",
	plugin_insertdate_dateFormat : "%m/%d/%Y",
	plugin_insertdate_timeFormat : "%H:%M:%S",
valid_elements : "@[id|class|style|title|dir<ltr?rtl|lang|xml::lang|onclick|ondblclick|"
+ "onmousedown|onmouseup|onmouseover|onmousemove|onmouseout|onkeypress|"
+ "onkeydown|onkeyup],a[rel|rev|charset|hreflang|tabindex|accesskey|type|"
+ "name|href|target|title|class|onfocus|onblur],strong/b,em/i,strike,u,"
+ "#p,-ol[type|compact],-ul[type|compact],-li,br,img[longdesc|usemap|"
+ "src|border|alt=|title|hspace|vspace|width|height|align],-sub,-sup,"
+ "-blockquote,-table[border=0|cellspacing|cellpadding|width|frame|rules|"
+ "height|align|summary|bgcolor|background|bordercolor],-tr[rowspan|width|"
+ "height|align|valign|bgcolor|background|bordercolor],tbody,thead,tfoot,"
+ "#td[colspan|rowspan|width|height|align|valign|bgcolor|background|bordercolor"
+ "|scope],#th[colspan|rowspan|width|height|align|valign|scope],caption,-div,"
+ "-span,-code,-pre,address,-h1,-h2,-h3,-h4,-h5,-h6,hr[size|noshade],-font[face"
+ "|size|color],dd,dl,dt,cite,abbr,acronym,del[datetime|cite],ins[datetime|cite],"
+ "object[classid|width|height|codebase|*],param[name|value|_value],embed[type|width"
+ "|height|src|*],script[src|type],map[name],area[shape|coords|href|alt|target],bdo,"
+ "button,col[align|char|charoff|span|valign|width],colgroup[align|char|charoff|span|"
+ "valign|width],dfn,fieldset,form[action|accept|accept-charset|enctype|method],"
+ "input[accept|alt|checked|disabled|maxlength|name|readonly|size|src|type|value],"
+ "kbd,label[for],legend,noscript,optgroup[label|disabled],option[disabled|label|selected|value],"
+ "q[cite],samp,select[disabled|multiple|name|size],small,"
+ "textarea[cols|rows|disabled|name|readonly],tt,var,big,"
+ "iframe[src|width|height|name|align]",
	fullscreen_settings : {
		theme_advanced_path_location : "top",
		theme_advanced_buttons1 : "fullscreen,separator,preview,separator,media,cut,copy,paste,separator,undo,redo,separator,search,replace,separator,code,separator,cleanup,separator,bold,italic,underline,strikethrough,separator,forecolor,backcolor,separator,justifyleft,justifycenter,justifyright,justifyfull,separator,help",
		theme_advanced_buttons2 : "removeformat,styleselect,formatselect,fontselect,fontsizeselect,separator,bullist,numlist,outdent,indent,hiddenchars,link,unlink,anchor",
		theme_advanced_buttons3 : "sub,sup,separator,image,insertdate,inserttime,separator,tablecontrols,separator,hr,advhr,visualaid,separator,charmap,emotions,iespell,flash,separator,print"
	}
});
