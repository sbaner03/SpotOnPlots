import pandas as pd
import numpy as np
from datetime import datetime,timedelta,date
import plotly.plotly as py
import plotly.graph_objs as go
from itertools import product
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.figure_factory as ff

dd = pd.read_csv('duedatediag.csv')
dd = dd.rename( columns={"DOCKNO": "Failed", "TOTAL": "Total"})
dd['Org'] = dd.apply(lambda x: x['specific_pt'].split('-')[0],axis=1)
dd['Dest'] = dd.apply(lambda x: x['specific_pt'].split('-')[1],axis=1)
virtuallocs = ['AMCF','AMDO','BBIB','BDQB','IXGF','BLRF','BWDB','BRGO','CCC','CJBC','DELO','GZBB','HYDO','IDRB','JAIC','JLRB','KNB','LKOB','MAAC','NAGB','PLGB','PNQO','PNQK','RPRB','SMBF','SNRB','VPIB','VGAF','SLMF','BHOB']
dd['Reason'] = dd.apply(lambda x: 'Virtual' if x['Org'] in virtuallocs or x['Dest'] in virtuallocs else x['Reason'], axis=1)
dd['Date'] = dd.apply(lambda x: datetime.strptime(x['Timestamp'],"%d/%m/%y"),axis=1)
loclist = list(dd['Org'].unique())+list(dd['Dest'].unique())

def generatepivot(df,reason,org,threshold,startdate=None,enddate=None):

    if not startdate:
        startdate = min(dd['Date'])
    else:
        startdate = datetime.strptime(startdate,'%d-%m-%Y')
    if not enddate:
        enddate = max(dd['Date'])
    else:
        enddate = datetime.strptime(enddate,'%d-%m-%Y')
    ### this is where we insert a database query to get the latest due date diagnostic results
    if org ==['All']:
        orglist = loclist
    else:
        orglist = org
    df = df[(df['Date']>=startdate)&(df['Date']<=enddate)]
    df = df[df['Reason']==reason]
    df = df[df['Org'].isin(orglist)]
    pivot = df.pivot_table(index = ['specific_pt','Org'], values = ['Total','Failed'], aggfunc=np.sum).reset_index()
    pivot['Perc'] = pivot.apply(lambda x: np.round(x['Failed']*100.0/x['Total'],2),axis=1)
    pivot = pivot.sort_values(['Failed', 'Total'], ascending=[False, False])
    return pivot

def printfigs(df,reason,org, threshold,startdate=None,enddate=None):
    pivot = generatepivot(df,reason,org, threshold,startdate=None,enddate=None)
    finalperc = np.round(pivot['Failed'].sum()*100.0/pivot['Total'].sum(),2)
    total = pivot['Total'].sum()
    pivot = pivot[pivot['Total']>=threshold]

    data = []
    for counter, org in enumerate(pivot['Org'].unique()):
        if reason == 'Virtual' and org in virtuallocs:
            markerdata = dict(size = 10,color = 'rgb(255,69,0,0.9)')
        elif reason == 'Virtual':
            markerdata = dict(size = 10,color = 'rgba(27, 224, 68, 0.7)')
        else:
            markerdata = dict(size = 10) ### map the regioncode here later
        trace = go.Scatter(
            x = pivot[pivot['Org']==org]['Failed'],
            y = pivot[pivot['Org']==org]['Perc'],
            name = org,
            mode = 'markers',
            marker = markerdata,
            ### the color should be linked to the org's region for location
            text= pivot[pivot['Org']==org]['specific_pt']
            )
        data.append(trace)


    layout = dict(title = '{0} failure {1}% out of {2} cons'.format(reason,np.round(finalperc,0),total),
                    paper_bgcolor = '#FFFAFA',
                    plot_bgcolor = '#FFFAFA',
                  yaxis = dict(title = 'Failure Percentage', zeroline = True),
                  xaxis = dict(title = 'Failed Cons', zeroline = True)
                 )

    fig = dict(data=data, layout=layout)
    return fig

app = dash.Dash()
# Append an externally hosted CSS stylesheet
my_css_url = "https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css"
app.css.append_css({
    "external_url": my_css_url
})

threshold = 17
fig = printfigs(dd,'Virtual',['All'], threshold)

startdate = datetime.strftime(min(dd['Date']),'%d-%m')
enddate = datetime.strftime(max(dd['Date']),'%d-%m')
table = ff.create_table(generatepivot(dd.head(10),'Virtual',['All'],threshold,startdate=None,enddate=None))

displaydiv = html.Div(className = 'container-fluid',children=[
    html.H1(className = "h3",children='Due Date Diagnostic from {0} to {1}'.format(startdate,enddate)),
    dcc.Graph(id='graph',figure = fig),
    dcc.Graph(id='table',figure = table)
])



selectiondiv = html.Div(className = 'container-fluid', children=[
html.Img(className="img-responsive",
    src = 'http://www.spoton.co.in/images/spoton.jpg'),
html.Label('Select Reason'),
dcc.Dropdown(
    className = 'btn btn-primary btn-lg btn-block',
    id = 'reason_selection',
    options=[{'label': i, 'value': i} for i in ['LH','Location','Virtual']],
    value='Virtual',
),
html.Label('Select # of Rows'),
dcc.Dropdown(
    className = 'btn btn-primary btn-lg btn-block',
    id = 'table_filter',
    options=[{'label': i, 'value': i} for i in ['Top10','Top25','All']],
    value='Top10',
),
html.Label('Select Origin'),
dcc.Dropdown(
className = 'btn btn-primary',
id = 'org_selector',
options = [{'label': i, 'value': i} for i in list(dd['Org'].unique())+['All']],
value = ['All'],
multi = True)])

app.layout = html.Div(className='row', children=[html.Div(className = 'col-sm-2',children = [selectiondiv]),html.Div(className= 'col-sm-10',children = [displaydiv])])

@app.callback(
    Output(component_id='graph',component_property = 'figure'),
    [Input(component_id='reason_selection', component_property='value'),
    Input(component_id='org_selector', component_property='value')]
)
def updatechart(reason,org):
    fig = printfigs(dd,reason,org,threshold)
    return fig

@app.callback(
    Output(component_id='table',component_property = 'figure'),
    [Input(component_id='reason_selection', component_property='value'),
    Input(component_id='table_filter', component_property='value'),
    Input(component_id='org_selector', component_property='value')]
)
def updatechart2(reason,table_filter,org):
    pivot = generatepivot(dd,reason,org,threshold,startdate=None,enddate=None)
    pivot = pivot[pivot['Total']>=threshold]
    pivot = pivot.rename(columns = {'specific_pt': 'Lane'})
    if table_filter=='All':
        pass
    elif table_filter=='Top10':
        pivot = pivot.head(10)
    else:
        pivot = pivot.head(25)

    table = ff.create_table(pivot)
    return table


app.run_server(debug=True)
