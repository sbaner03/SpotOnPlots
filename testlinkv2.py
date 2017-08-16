import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.figure_factory as ff
from dash.dependencies import Input, Output

from duediagpage import makepage_dd
from spotonDD import duedatediag
from spotonddplot import dd_generatepivot
from spotonddplot import dd_printfigs

from lhplanningpage import makepage_lhplanning
from spotonLH import lhdata

app = dash.Dash()
app.config.supress_callback_exceptions = True
my_css_url = "https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css"
app.css.append_css({
    "external_url": my_css_url
})


lh = lhdata()
a,b = lh.returngraphs(['BOMH'],['DELH'])
print (a)
app.layout = html.Div(className= 'test',children = dcc.Graph(id='graph',figure = a))

app.run_server(debug=True)
