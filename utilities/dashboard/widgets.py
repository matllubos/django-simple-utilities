# coding: utf-8
from django.utils.safestring import mark_safe
from django.utils.encoding import force_unicode


class DashboardWidget(object):
        
    def _id(self):
        return '%s-%s' % (self.prefix, self.name)
    id = property(_id)
    
    
    def render(self, value, title, measure=None):
        return mark_safe(u'<table id="dashboard-%s"><th>%s:</th><td>%s %s</td></table>' % (self.id, force_unicode(title), force_unicode(value), force_unicode(measure)))
    
    
    
class TableDashboardWidget(DashboardWidget):
    
    def render_title(self, title):
        return u'<tr><th colspan="2">%s</th></tr>' % title
    
    def render(self, values, title, measure=None):
        rows = []      
        rows.append(self.render_title(title))
        
        for key, value in values.items():
            rows.append(u'<tr><td>%s</td><td>%s %s</td></tr>' % (force_unicode(key), force_unicode(value), force_unicode(measure))) 
        return mark_safe(u'<table id="dashboard-%s">%s</table>' % (self.id, u'\n'.join(rows)))
    
    
class BarGraphDashboardWidget(DashboardWidget):

    def render_title(self, title):
        return u'<tr><th>%s</th></tr>' % title
        
    def render(self, values, title, measure=None):
        rows = []      
        rows.append(self.render_title(title))
        
        rows.append(u'<tr><td><div id="chart-%s" style="margin-top:20px; margin-left:20px; width:350px; height:300px;"></div></td></tr>' % (self.id)) 
        
        graph_data = []
        for key, value in values.items():
            graph_data.append("['%s', %s]" % (force_unicode(key), force_unicode(value)))
            
        
        
        rows.append(u'<script class="code" type="text/javascript">$(document).ready(function(){\n\
                        $.jqplot.config.enablePlugins = true;\n\
                            var values = [%s];\n\
                            \n\
                            plot1 = $.jqplot(\'%s\', [values], {\n\
                            // Only animate if we\'re not using excanvas (not in IE 7 or IE 8)..\n\
                            animate: !$.jqplot.use_excanvas,\n\
                            series:[{renderer:$.jqplot.BarRenderer}], \n\
                            axesDefaults: {\n\
                                tickRenderer: $.jqplot.CanvasAxisTickRenderer ,\n\
                                tickOptions: { \n\
                                  fontSize: \'11pt\'\n\
                                }\n\
                            },\n\
                            seriesDefaults:{\n\
                                renderer:$.jqplot.BarRenderer,\n\
                                rendererOptions: { fillToZero: true },\n\
                                pointLabels: { show: true }\n\
                            },\n\
                            axes: {\n\
                              xaxis: {\n\
                                renderer: $.jqplot.CategoryAxisRenderer,\n\
                                tickOptions: {\n\
                                    angle: -30,\n\
                                }\n\
                              }\n\
                            }\n\
                        });\n\
                    });</script>' % (u', '.join(graph_data), 'chart-%s' % self.id))
        return mark_safe(u'<table id="dashboard-%s">%s</table>' % (self.id, u'\n'.join(rows)))
        
        
        
        
        