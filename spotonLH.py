
import pandas as pd
import numpy as np
from datetime import datetime,timedelta,date
import plotly.plotly as py
import plotly.graph_objs as go
from itertools import product
import plotly.figure_factory as ff
import ast

class lhdata():
    def __init__(self):
        self.edges = pd.read_csv('checkedge.csv')
        self.edges = self.edges.rename(columns = {'Jul-15 to Aug08': 'CurrMonth'})
        self.col = 'CurrMonth'
        series = pd.Series([ast.literal_eval(i) for i in self.edges['areabrkup']])
        srdf= pd.DataFrame(series, columns = ['AreaSplit'])
        self.edges = self.edges.merge(srdf, left_index=True, right_index=True)
        self.startdate = datetime.strptime('15-07-2017','%d-%m-%Y')
        self.enddate = datetime.strptime('08-08-2017','%d-%m-%Y')
        self.orglist = list(self.edges['Origin'].unique())
        self.destlist = list(self.edges['Destn'].unique())
        self.orgoptions = [{'label': i, 'value': i} for i in self.orglist]
        self.destoptions = [{'label': i, 'value': i} for i in self.destlist]


    def printheatmap (self,areadict):
        heatmapdf = pd.DataFrame([[None,None,None]], columns=['OrgArea','DestArea','Wt'])
        for count, keys in enumerate(list(areadict.keys())):
            datalist = []
            hmdict = areadict.get(keys)[0]
            hmdf = pd.DataFrame.from_dict(hmdict, orient='index', dtype=None)
            hmdf = hmdf.reset_index()
            hmdf.columns = ['Area','Wt']
            hmdf['OrgArea'] = hmdf.apply(lambda x: x['Area'].split('-')[0],axis=1)
            hmdf['DestArea'] = hmdf.apply(lambda x: x['Area'].split('-')[1],axis=1)
            hmdf = hmdf[heatmapdf.columns]
            heatmapdf = heatmapdf.append(hmdf)
        heatmapdf = heatmapdf.dropna()
        heatmappivot = heatmapdf.pivot_table(index = 'OrgArea', values = 'Wt', columns = 'DestArea', aggfunc = pd.np.sum)
        heatmappivot = heatmappivot.fillna(0.0).T
        x = list(heatmappivot.columns)
        y = list(heatmappivot.index)
        z = heatmappivot.values
        z_text = np.around(z,decimals=1)
        xaxis = {'dtick': 1,'gridcolor': 'rgb(0, 0, 0)','side': 'bottom','ticks': ''}
        heatmapfig = ff.create_annotated_heatmap(z, x=x, y=y, annotation_text=z_text, colorscale='Viridis')
        for i in range(len(heatmapfig.layout.annotations)):
            heatmapfig.layout.annotations[i].font.size = 10
        heatmapfig.layout.title = 'Load Table in Mt - XAxis OrgArea YAxis DestArea'
        heatmapfig.layout.xaxis = xaxis
        return heatmapfig

    def lh_printfigs (self,orglist,destlist):
        reporttitle = 'Linehaul Edge Data'
        runlist = [i for i in product(orglist,destlist)]
        datalist = []
        areadict = {}
        col = 'CurrMonth'
        for i in runlist:
            org = i[0]
            dest = i[1]

            try:
                fl= self.edges[(self.edges['Origin']==org)&(self.edges['Destn']==dest)]
                bl= self.edges[(self.edges['Origin']==dest)&(self.edges['Destn']==org)]
                print (col)
                for df in [fl,bl]:
                    org = (list(df['Origin'])[0])
                    dest = (list(df['Destn'])[0])
                    ydata = (list(df[col])[0])
                    var = (list(df['Var'])[0])
                    areasplit = list(df['AreaSplit'].values)
                    areadict.update({(org,dest): areasplit})

                    trace = go.Bar(
                    x = '{0}-{1}'.format(org,dest),
                    y = ydata,
                    text = 'Edge: {0}, Var: {1}'.format(ydata,var),
                    textposition='bottom',
                    name = '{0}-{1}'.format(org,dest)
                    )
                    datalist.append(trace)
            except:
                pass
        layout = go.Layout(
            title=reporttitle
        )

        self.barfig = go.Figure(data=datalist, layout=layout)
        self.heatmapfig = self.printheatmap(areadict)

    def returngraphs(self,orglist,destlist):
        self.lh_printfigs(orglist,destlist)
        return self.barfig,self.heatmapfig
