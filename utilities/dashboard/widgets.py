# coding: utf-8
from django.utils.safestring import mark_safe
from django.utils.encoding import force_unicode
from django.conf import settings

    
    

class DashboardWidget(object):
        
    def _id(self):
        return '%s-%s' % (self.prefix, self.name)
    id = property(_id)
    
    
    def render(self, value, title, measure=None):
        return mark_safe(u'<table id="dashboard-%s"><th>%s:</th><td>%s %s</td></table>' % (self.id, force_unicode(title), force_unicode(value), force_unicode(measure)))
    
    def get_media(self, media):
        for js in self.Media.js:
            if not js in media['js']:
                media['js'].append(js)
                
        for css in self.Media.css.get('print', []):
            if not css in media['css']['print']:
                media['css']['print'].append(css)
        
        for css in self.Media.css.get('screen', []):
            if not css in media['css']['screen']:
                media['css']['screen'].append(css)        
        
        return media
        
    class Media():
        js = []
        css = {'print': [], 'screen': []}
    
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
        
        rows.append(u'<tr><td><div id="chart-%s" style="margin-top:20px; margin-left:20px; width:350px; height:300px;"></div>' % (self.id)) 
        
        graph_data = []
        for key, value in values.items():
            graph_data.append("['%s', %s]" % (force_unicode(key), force_unicode(value)))
            
        
        
        rows.append(u'<script class="code" type="text/javascript">$(document).ready(function(){\n\
                        $.jqplot.config.enablePlugins = true;\n\
                            var values_%s = [%s];\n\
                            \n\
                            plot_%s = $.jqplot(\'%s\', [values_%s], {\n\
                            seriesDefaults:{\n\
                                renderer:$.jqplot.BarRenderer,\n\
                            },\n\
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
                    });</script>' % (self.id.replace('-', '_'),u','.join(graph_data), self.id.replace('-', '_'), 'chart-%s' % self.id, self.id.replace('-', '_'),))
        
        rows.append('</td></tr>')
        return mark_safe(u'<table id="dashboard-%s">%s</table>' % (self.id, u'\n'.join(rows)))
    
    class Media():
        js = (
              '%sutilities/js/jquery-1.6.4.min.js' % settings.STATIC_URL,
              '%sutilities/jqplot/js/jquery.jqplot.min.js' % settings.STATIC_URL,
              '%sutilities/jqplot/js/plugins/jqplot.barRenderer.min.js' % settings.STATIC_URL,
              '%sutilities/jqplot/js/plugins/jqplot.pieRenderer.min.js' % settings.STATIC_URL,
              '%sutilities/jqplot/js/plugins/jqplot.categoryAxisRenderer.min.js' % settings.STATIC_URL,
              '%sutilities/jqplot/js/plugins/jqplot.dateAxisRenderer.min.js' % settings.STATIC_URL,
              '%sutilities/jqplot/js/plugins/jqplot.logAxisRenderer.min.js' % settings.STATIC_URL,
              '%sutilities/jqplot/js/plugins/jqplot.canvasTextRenderer.min.js' % settings.STATIC_URL,
              '%sutilities/jqplot/js/plugins/jqplot.canvasAxisLabelRenderer.min.js' % settings.STATIC_URL,
              '%sutilities/jqplot/js/plugins/jqplot.canvasAxisTickRenderer.min.js' % settings.STATIC_URL,
              '%sutilities/jqplot/js/plugins/jqplot.categoryAxisRenderer.min.js' % settings.STATIC_URL,
              '%sutilities/jqplot/js/plugins/jqplot.pointLabels.min.js' % settings.STATIC_URL,
              '%sutilities/jqplot/js/plugins/jqplot.dateAxisRenderer.min.js' % settings.STATIC_URL,

        )
        css = {'screen': (
                      '%sutilities/jqplot/css/jquery.jqplot.min.css' % settings.STATIC_URL,
                      '%sutilities/jqplot/css/dashboard.css' % settings.STATIC_URL,      
                      )}
        
        
        
        